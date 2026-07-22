"""
实战1 - CLI文件整理工具
运行方式: python examples/file_organizer.py [目录路径] [--dry-run]

综合运用: dataclass, Enum, ABC, property, 上下文管理器, pathlib, argparse
功能: 按文件类型自动归类到子目录
"""

import argparse
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from abc import ABC, abstractmethod


# ============================================================
# 数据模型
# ============================================================

class FileCategory(Enum):
    IMAGE = "图片"
    VIDEO = "视频"
    AUDIO = "音频"
    DOCUMENT = "文档"
    ARCHIVE = "压缩包"
    CODE = "代码"
    OTHER = "其他"


# 扩展名 -> 分类 映射
EXTENSION_MAP: dict[str, FileCategory] = {
    ".jpg": FileCategory.IMAGE, ".jpeg": FileCategory.IMAGE,
    ".png": FileCategory.IMAGE, ".gif": FileCategory.IMAGE,
    ".svg": FileCategory.IMAGE, ".webp": FileCategory.IMAGE,
    ".mp4": FileCategory.VIDEO, ".avi": FileCategory.VIDEO,
    ".mkv": FileCategory.VIDEO, ".mov": FileCategory.VIDEO,
    ".mp3": FileCategory.AUDIO, ".wav": FileCategory.AUDIO,
    ".flac": FileCategory.AUDIO, ".ogg": FileCategory.AUDIO,
    ".pdf": FileCategory.DOCUMENT, ".doc": FileCategory.DOCUMENT,
    ".docx": FileCategory.DOCUMENT, ".txt": FileCategory.DOCUMENT,
    ".md": FileCategory.DOCUMENT, ".xlsx": FileCategory.DOCUMENT,
    ".zip": FileCategory.ARCHIVE, ".tar": FileCategory.ARCHIVE,
    ".gz": FileCategory.ARCHIVE, ".7z": FileCategory.ARCHIVE,
    ".rar": FileCategory.ARCHIVE,
    ".py": FileCategory.CODE, ".js": FileCategory.CODE,
    ".ts": FileCategory.CODE, ".go": FileCategory.CODE,
    ".rs": FileCategory.CODE, ".java": FileCategory.CODE,
    ".c": FileCategory.CODE, ".cpp": FileCategory.CODE,
}


@dataclass
class FileInfo:
    path: Path
    size: int
    category: FileCategory

    @property
    def human_size(self) -> str:
        if self.size >= 1024 * 1024:
            return f"{self.size / 1024 / 1024:.1f}MB"
        elif self.size >= 1024:
            return f"{self.size / 1024:.1f}KB"
        return f"{self.size}B"

    @classmethod
    def from_path(cls, path: Path) -> "FileInfo":
        ext = path.suffix.lower()
        category = EXTENSION_MAP.get(ext, FileCategory.OTHER)
        return cls(path=path, size=path.stat().st_size, category=category)


@dataclass
class OrganizeResult:
    moved: list[tuple[Path, Path]] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    errors: list[tuple[Path, str]] = field(default_factory=list)

    @property
    def total_moved(self) -> int:
        return len(self.moved)

    def summary(self) -> str:
        lines = [
            f"移动: {len(self.moved)} 个文件",
            f"跳过: {len(self.skipped)} 个",
            f"失败: {len(self.errors)} 个",
        ]
        return "\n".join(lines)


# ============================================================
# 策略模式：不同的整理策略
# ============================================================

class OrganizeStrategy(ABC):
    @abstractmethod
    def target_dir(self, file: FileInfo, base_dir: Path) -> Path:
        ...


class ByCategoryStrategy(OrganizeStrategy):
    """按类型分目录: 图片/, 文档/, 代码/ ..."""

    def target_dir(self, file: FileInfo, base_dir: Path) -> Path:
        return base_dir / file.category.value


class ByExtensionStrategy(OrganizeStrategy):
    """按扩展名分目录: .jpg/, .pdf/, .py/ ..."""

    def target_dir(self, file: FileInfo, base_dir: Path) -> Path:
        ext = file.path.suffix.lower() or "无扩展名"
        return base_dir / ext


# ============================================================
# 核心引擎
# ============================================================

class FileOrganizer:
    def __init__(self, strategy: OrganizeStrategy, dry_run: bool = False):
        self.strategy = strategy
        self.dry_run = dry_run

    def scan(self, directory: Path) -> list[FileInfo]:
        """扫描目录下的文件（不递归）"""
        files = []
        for item in directory.iterdir():
            if item.is_file() and not item.name.startswith("."):
                files.append(FileInfo.from_path(item))
        return files

    def organize(self, directory: Path) -> OrganizeResult:
        result = OrganizeResult()
        files = self.scan(directory)

        for file_info in files:
            target_dir = self.strategy.target_dir(file_info, directory)
            target_path = target_dir / file_info.path.name

            # 跳过已在正确位置的文件
            if file_info.path.parent == target_dir:
                result.skipped.append(file_info.path)
                continue

            # 处理同名文件
            target_path = self._resolve_conflict(target_path)

            try:
                if not self.dry_run:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_info.path), str(target_path))
                result.moved.append((file_info.path, target_path))
            except OSError as e:
                result.errors.append((file_info.path, str(e)))

        return result

    def _resolve_conflict(self, target: Path) -> Path:
        """同名文件加序号: file.txt -> file_1.txt"""
        if not target.exists():
            return target
        stem = target.stem
        suffix = target.suffix
        counter = 1
        while True:
            new_target = target.parent / f"{stem}_{counter}{suffix}"
            if not new_target.exists():
                return new_target
            counter += 1


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="按类型整理文件到子目录")
    parser.add_argument("directory", nargs="?", default=".", help="要整理的目录")
    parser.add_argument("--dry-run", action="store_true", help="只显示结果，不实际移动")
    parser.add_argument(
        "--strategy", choices=["category", "extension"],
        default="category", help="整理策略"
    )
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        print(f"错误: '{directory}' 不是有效目录")
        sys.exit(1)

    strategy = (
        ByCategoryStrategy() if args.strategy == "category"
        else ByExtensionStrategy()
    )

    organizer = FileOrganizer(strategy, dry_run=args.dry_run)

    if args.dry_run:
        print("[预览模式] 不会实际移动文件\n")

    # 先展示扫描结果
    files = organizer.scan(directory)
    if not files:
        print("目录下没有需要整理的文件")
        return

    print(f"扫描到 {len(files)} 个文件:\n")
    for f in sorted(files, key=lambda x: x.category.value):
        print(f"  {f.category.value:<6} {f.human_size:>8}  {f.path.name}")

    print()
    result = organizer.organize(directory)
    print(result.summary())

    if result.moved:
        print("\n移动详情:")
        for src, dst in result.moved:
            print(f"  {src.name} -> {dst.relative_to(directory)}")


if __name__ == "__main__":
    main()
