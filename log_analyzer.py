"""
实战3 - 日志分析器
运行方式: python examples/log_analyzer.py [日志文件路径]

综合运用: 生成器, 正则, dataclass, 策略模式, 迭代器协议, 上下文管理器
功能: 解析日志、统计错误、按时间/级别过滤、生成报告
"""

import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Callable, Iterator, Optional


# ============================================================
# 数据模型
# ============================================================

class LogLevel(IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


@dataclass(frozen=True)
class LogEntry:
    timestamp: datetime
    level: LogLevel
    message: str
    source: str = ""

    @property
    def is_error(self) -> bool:
        return self.level >= LogLevel.ERROR

    def __str__(self):
        ts = self.timestamp.strftime("%H:%M:%S")
        return f"[{ts}] {self.level.name:<8} {self.message}"


@dataclass
class LogStats:
    total: int = 0
    by_level: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_source: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    error_messages: list[str] = field(default_factory=list)
    time_range: tuple[Optional[datetime], Optional[datetime]] = (None, None)

    def summary(self) -> str:
        lines = [
            "=" * 50,
            "日志分析报告",
            "=" * 50,
            f"总条目: {self.total}",
            f"时间范围: {self.time_range[0]} ~ {self.time_range[1]}",
            "",
            "按级别统计:",
        ]
        for level in LogLevel:
            count = self.by_level.get(level.name, 0)
            bar = "█" * (count // max(1, self.total // 20))
            lines.append(f"  {level.name:<10} {count:>6}  {bar}")

        if self.by_source:
            lines.append("\n按来源统计 (Top 5):")
            sorted_sources = sorted(
                self.by_source.items(), key=lambda x: x[1], reverse=True
            )[:5]
            for source, count in sorted_sources:
                lines.append(f"  {source:<20} {count:>6}")

        if self.error_messages:
            lines.append(f"\n最近错误 (最多显示5条):")
            for msg in self.error_messages[-5:]:
                lines.append(f"  ! {msg}")

        lines.append("=" * 50)
        return "\n".join(lines)


# ============================================================
# 日志解析器（生成器）
# ============================================================

# 支持的日志格式
PATTERNS = [
    # 2026-07-22 10:30:00 ERROR [module] message
    re.compile(
        r"(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
        r"(?P<level>\w+)\s+"
        r"\[(?P<source>[^\]]*)\]\s+"
        r"(?P<msg>.+)"
    ),
    # [2026-07-22 10:30:00] LEVEL: message
    re.compile(
        r"\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+"
        r"(?P<level>\w+):\s+"
        r"(?P<msg>.+)"
    ),
    # LEVEL 2026-07-22 10:30:00 message
    re.compile(
        r"(?P<level>\w+)\s+"
        r"(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
        r"(?P<msg>.+)"
    ),
]


def parse_line(line: str) -> Optional[LogEntry]:
    """尝试用多种格式解析一行日志"""
    line = line.strip()
    if not line:
        return None

    for pattern in PATTERNS:
        match = pattern.match(line)
        if match:
            groups = match.groupdict()
            try:
                ts = datetime.strptime(groups["ts"], "%Y-%m-%d %H:%M:%S")
                level = LogLevel[groups["level"].upper()]
                return LogEntry(
                    timestamp=ts,
                    level=level,
                    message=groups["msg"],
                    source=groups.get("source", ""),
                )
            except (KeyError, ValueError):
                continue
    return None


def parse_file(filepath: Path) -> Iterator[LogEntry]:
    """生成器：逐行解析日志文件（内存友好）"""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            entry = parse_line(line)
            if entry:
                yield entry


# ============================================================
# 过滤器（可组合）
# ============================================================

class LogFilter:
    """可组合的日志过滤器"""

    def __init__(self, predicate: Callable[[LogEntry], bool]):
        self._predicate = predicate

    def __call__(self, entry: LogEntry) -> bool:
        return self._predicate(entry)

    def __and__(self, other: "LogFilter") -> "LogFilter":
        return LogFilter(lambda e: self(e) and other(e))

    def __or__(self, other: "LogFilter") -> "LogFilter":
        return LogFilter(lambda e: self(e) or other(e))

    def __invert__(self) -> "LogFilter":
        return LogFilter(lambda e: not self(e))


# 预定义过滤器
def level_filter(min_level: LogLevel) -> LogFilter:
    return LogFilter(lambda e: e.level >= min_level)


def time_range_filter(start: str, end: str) -> LogFilter:
    start_dt = datetime.strptime(start, "%H:%M:%S")
    end_dt = datetime.strptime(end, "%H:%M:%S")
    return LogFilter(
        lambda e: start_dt <= e.timestamp.replace(year=1900, month=1, day=1) <= end_dt
    )


def keyword_filter(keyword: str) -> LogFilter:
    return LogFilter(lambda e: keyword.lower() in e.message.lower())


def source_filter(source: str) -> LogFilter:
    return LogFilter(lambda e: source.lower() in e.source.lower())


def apply_filter(entries: Iterator[LogEntry], f: LogFilter) -> Iterator[LogEntry]:
    """生成器：过滤日志流"""
    for entry in entries:
        if f(entry):
            yield entry


# ============================================================
# 分析引擎
# ============================================================

class LogAnalyzer:
    def __init__(self):
        self._entries: list[LogEntry] = []

    def load(self, filepath: str | Path):
        """加载日志文件"""
        filepath = Path(filepath)
        self._entries = list(parse_file(filepath))
        print(f"已加载 {len(self._entries)} 条日志")

    def load_entries(self, entries: list[LogEntry]):
        self._entries = entries

    @property
    def entries(self) -> list[LogEntry]:
        return self._entries

    def filter(self, f: LogFilter) -> "LogAnalyzer":
        """返回新的 Analyzer，只包含过滤后的条目"""
        new = LogAnalyzer()
        new._entries = [e for e in self._entries if f(e)]
        return new

    def stats(self) -> LogStats:
        """生成统计信息"""
        s = LogStats(total=len(self._entries))
        if not self._entries:
            return s

        s.time_range = (self._entries[0].timestamp, self._entries[-1].timestamp)

        for entry in self._entries:
            s.by_level[entry.level.name] += 1
            if entry.source:
                s.by_source[entry.source] += 1
            if entry.is_error:
                s.error_messages.append(entry.message)

        return s

    def group_by(self, key: Callable[[LogEntry], str]) -> dict[str, list[LogEntry]]:
        """按指定键分组"""
        groups: dict[str, list[LogEntry]] = defaultdict(list)
        for entry in self._entries:
            groups[key(entry)].append(entry)
        return dict(groups)

    def top_errors(self, n: int = 10) -> list[tuple[str, int]]:
        """出现最多的错误消息"""
        counter: dict[str, int] = defaultdict(int)
        for entry in self._entries:
            if entry.is_error:
                counter[entry.message] += 1
        return sorted(counter.items(), key=lambda x: x[1], reverse=True)[:n]


# ============================================================
# 演示
# ============================================================

def generate_sample_log(filepath: Path):
    """生成示例日志文件"""
    import random
    random.seed(42)

    levels = ["DEBUG", "INFO", "INFO", "INFO", "WARNING", "ERROR", "CRITICAL"]
    sources = ["auth", "database", "api", "cache", "scheduler"]
    messages = {
        "DEBUG": ["变量 x=42", "进入函数 process()", "缓存命中"],
        "INFO": ["用户登录成功", "请求处理完成", "定时任务执行", "服务启动"],
        "WARNING": ["响应时间超过2s", "内存使用率80%", "重试第2次"],
        "ERROR": ["数据库连接超时", "空指针异常", "文件不存在: /tmp/data.csv"],
        "CRITICAL": ["服务崩溃", "磁盘空间不足"],
    }

    lines = []
    for i in range(200):
        hour = 8 + i // 30
        minute = i % 60
        second = random.randint(0, 59)
        level = random.choice(levels)
        source = random.choice(sources)
        msg = random.choice(messages[level])
        lines.append(f"2026-07-22 {hour:02d}:{minute:02d}:{second:02d} {level} [{source}] {msg}")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成示例日志: {filepath} ({len(lines)} 行)")


def main():
    log_path = Path("/tmp/sample_app.log")

    # 如果没提供日志文件，生成示例
    if len(sys.argv) > 1:
        log_path = Path(sys.argv[1])
        if not log_path.exists():
            print(f"文件不存在: {log_path}")
            sys.exit(1)
    else:
        generate_sample_log(log_path)

    print()

    # 加载并分析
    analyzer = LogAnalyzer()
    analyzer.load(log_path)

    # 全量统计
    print(analyzer.stats().summary())

    # 只看错误
    print("\n--- 只看 ERROR 及以上 ---")
    errors = analyzer.filter(level_filter(LogLevel.ERROR))
    print(f"错误条目: {len(errors.entries)}")
    for entry in errors.entries[:5]:
        print(f"  {entry}")

    # 组合过滤：database 模块的警告
    print("\n--- database 模块的 WARNING ---")
    db_warnings = analyzer.filter(
        source_filter("database") & level_filter(LogLevel.WARNING)
    )
    for entry in db_warnings.entries[:5]:
        print(f"  {entry}")

    # 关键词搜索
    print("\n--- 包含 '超时' 的日志 ---")
    timeout_logs = analyzer.filter(keyword_filter("超时"))
    for entry in timeout_logs.entries[:5]:
        print(f"  {entry}")

    # Top 错误
    print("\n--- 出现最多的错误 ---")
    for msg, count in analyzer.top_errors(5):
        print(f"  [{count}次] {msg}")

    # 按来源分组统计
    print("\n--- 按来源分组 ---")
    groups = analyzer.group_by(lambda e: e.source or "unknown")
    for source, entries in sorted(groups.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {source:<15} {len(entries)} 条")


if __name__ == "__main__":
    main()
