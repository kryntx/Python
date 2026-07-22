"""
00 - Python 工具链：venv、pip、python 命令及隐藏技巧
运行方式: python3 00_toolchain.py（本章主要是命令参考，代码部分可直接运行）

建议：打开终端，边看边敲命令。
"""

# ============================================================
# 一、python3 命令本身
# ============================================================

"""
# 1. 查看版本和路径
python3 --version          # Python 3.x.x
python3 -c "import sys; print(sys.executable)"  # 解释器完整路径
which python3              # 命令位置
python3 -m site            # 查看所有包搜索路径

# 2. 交互模式
python3                    # 进入 REPL
python3 -i script.py       # 运行脚本后留在交互模式（方便调试）
python3 -q                 # 安静模式，不显示版本横幅

# 3. 直接执行代码
python3 -c "print(2**100)"
python3 -c "import json; print(json.dumps({'a':1}))"

# 4. 以模块方式运行（-m）—— 非常重要！
python3 -m http.server 8000    # 启动一个文件服务器
python3 -m json.tool data.json # 格式化 JSON
python3 -m venv myenv          # 创建虚拟环境
python3 -m pip install flask   # 用当前 python 对应的 pip 安装
python3 -m pdb script.py       # 调试器
python3 -m timeit "sum(range(1000))"  # 性能测试
python3 -m cProfile script.py  # 性能分析
python3 -m zipfile -l archive.zip     # 列出 zip 内容
python3 -m tarfile -l archive.tar.gz  # 列出 tar 内容
python3 -m py_compile script.py       # 编译为 .pyc 检查语法

# 5. 其他实用标志
python3 -u script.py       # 无缓冲输出（实时看到 print）
python3 -O script.py       # 优化模式（去掉 assert 和 __debug__）
python3 -B script.py       # 不生成 .pyc 文件
python3 -W error script.py # 把所有 warning 变成 error
python3 -X dev script.py   # 开发模式（更严格的检查）
python3 -E script.py       # 忽略环境变量（PYTHONPATH 等）
python3 -I script.py       # 隔离模式（忽略环境变量 + 用户包路径）

# 6. 查看帮助
python3 -h                 # 所有命令行选项
python3 -m module_name -h  # 模块帮助
"""

# ============================================================
# 二、venv 虚拟环境
# ============================================================

"""
# --- 为什么需要虚拟环境 ---
# 项目A需要 requests==2.25，项目B需要 requests==2.31
# 全局只能装一个版本 → 冲突！虚拟环境隔离依赖。

# --- 基本操作 ---
python3 -m venv myenv              # 创建（在当前目录生成 myenv/ 文件夹）
python3 -m venv --system-site-packages myenv  # 创建时可访问全局包
python3 -m venv --upgrade myenv    # 升级已有环境的 python 版本

# 激活
source myenv/bin/activate          # Linux/macOS
# myenv\Scripts\activate           # Windows

# 激活后的变化：
# - 命令行前面出现 (myenv) 前缀
# - python3 和 pip 指向环境内的版本
# - 安装的包只在这个环境里

# 停用
deactivate

# 删除：直接删文件夹即可
rm -rf myenv

# --- 环境内的重要路径 ---
myenv/
├── bin/            # python, pip, activate 等可执行文件
├── lib/
│   └── python3.x/
│       └── site-packages/  # 安装的第三方包都在这里
└── pyvenv.cfg      # 环境配置（指向基础 python）

# --- 实用技巧 ---
# 查看当前用的是哪个 python
python3 -c "import sys; print(sys.prefix)"

# 查看环境内安装了什么
pip list
pip freeze > requirements.txt   # 导出依赖

# 从 requirements.txt 恢复环境
python3 -m venv fresh_env
source fresh_env/bin/activate
pip install -r requirements.txt

# --- 不激活也能用（CI/脚本中常用）---
myenv/bin/python3 script.py
myenv/bin/pip install requests

# --- 多版本 Python 共存 ---
# 如果系统装了 python3.11 和 python3.12：
python3.11 -m venv env311
python3.12 -m venv env312
# 每个环境锁定创建时的 python 版本
"""

# ============================================================
# 三、pip 包管理
# ============================================================

"""
# --- 安装 ---
pip install requests              # 最新版
pip install requests==2.31.0     # 精确版本
pip install "requests>=2.28,<3"  # 版本范围（注意引号！shell 会解析 < >）
pip install -e .                  # 可编辑安装（开发自己的包时用）
pip install -e ".[dev]"          # 安装含 dev 额外依赖
pip install git+https://github.com/user/repo.git  # 从 git 安装
pip install ./local_package.whl  # 从本地文件安装

# --- 卸载/升级 ---
pip uninstall requests
pip install --upgrade requests
pip install --upgrade pip        # 升级 pip 自身（经常需要！）

# --- 查看信息 ---
pip list                         # 已安装的所有包
pip list --outdated              # 有更新可用的包
pip show requests                # 某个包的详细信息（版本、依赖、位置）
pip show -f requests             # 显示安装的所有文件
pip check                        # 检查依赖冲突

# --- requirements.txt ---
pip freeze > requirements.txt    # 导出当前环境所有包（精确版本）
pip install -r requirements.txt  # 从文件安装

# requirements.txt 格式示例：
# requests==2.31.0
# flask>=2.0
# numpy
# -e .                    # 可编辑安装当前目录
# -r other_requirements.txt  # 引用另一个文件

# --- 实用选项 ---
pip install --user package       # 装到用户目录（不需要 sudo）
pip install --target ./libs pkg  # 装到指定目录（打包部署用）
pip install --no-deps pkg        # 不装依赖（手动管理依赖时）
pip install --dry-run pkg        # 模拟安装，看会装什么（pip 22.2+）
pip download pkg -d ./wheels     # 只下载不安装（离线部署）
pip install --no-index --find-links ./wheels pkg  # 离线安装

# --- pip 配置 ---
# 配置文件位置: ~/.config/pip/pip.conf (Linux)
# 设置国内镜像加速：
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 临时使用镜像：
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple requests

# --- 缓存 ---
pip cache dir                    # 缓存目录
pip cache list                   # 缓存内容
pip cache purge                  # 清除缓存
pip install --no-cache-dir pkg   # 不用缓存
"""

# ============================================================
# 四、你可能不知道的隐藏技巧
# ============================================================

"""
# --- 1. PEP 723: 脚本内联依赖（Python 3.11+ / pip 24+）---
# 在脚本文件头部声明依赖，无需虚拟环境！
# 文件 my_script.py:
#
#   # /// script
#   # requires-python = ">=3.11"
#   # dependencies = [
#   #     "requests",
#   #     "rich",
#   # ]
#   # ///
#
#   import requests
#   from rich import print
#   ...
#
# 运行: pipx run my_script.py  或  uv run my_script.py
# pip 会自动创建临时环境安装依赖

# --- 2. python3 -m 的隐藏模块 ---
python3 -m antigravity       # 彩蛋：打开 xkcd 漫画
python3 -m this              # Python 之禅
python3 -m ensurepip         # 确保 pip 存在
python3 -m idlelib           # 启动 IDLE 编辑器
python3 -m webbrowser "https://docs.python.org"  # 用默认浏览器打开URL
python3 -m smtplib           # (不能直接运行，但可以 import)

# --- 3. REPL 中的技巧 ---
# 在交互模式中：
# _        → 上一个表达式的结果
# __       → 上上一个结果
# exit()   → 退出
# help()   → 交互帮助
# help(str.split)  → 查看某个方法的文档
# dir(obj) → 列出对象所有属性
# vars()   → 当前所有局部变量
# import antigravity  → 彩蛋

# --- 4. PYTHONPATH 和包搜索 ---
# 让你的模块在任何地方都能 import：
export PYTHONPATH="/home/iaa/mylibs:$PYTHONPATH"
# 或者在脚本中：
# import sys; sys.path.insert(0, "/path/to/my/libs")

# --- 5. .pth 文件：永久添加搜索路径 ---
# 在 site-packages/ 下放一个 my_paths.pth 文件：
# /home/iaa/mylibs
# /home/iaa/shared_modules
# 每行一个路径，python 启动时自动加入 sys.path

# --- 6. pip install -e 的真正用途 ---
# 开发自己的包时，不用每次改了代码都重新安装：
# cd my_project
# pip install -e .
# 之后 import my_project 直接读源码，改了就生效

# --- 7. 查看一个包装在哪 ---
python3 -c "import requests; print(requests.__file__)"
pip show -f requests | head -5

# --- 8. 快速启动 HTTP 文件服务器 ---
python3 -m http.server 8000           # 当前目录
python3 -m http.server 8000 -d /path  # 指定目录
python3 -m http.server --bind 127.0.0.1  # 只允许本机访问

# --- 9. 一行代码实用片段 ---
python3 -c "import uuid; print(uuid.uuid4())"          # 生成 UUID
python3 -c "import secrets; print(secrets.token_hex(16))"  # 随机 token
python3 -c "import platform; print(platform.platform())"   # 系统信息
python3 -c "import sys; print(sys.getsizeof([]))"          # 对象内存大小
python3 -c "import keyword; print(keyword.kwlist)"         # 所有关键字

# --- 10. 调试技巧 ---
# 在代码中插入断点（Python 3.7+）：
# breakpoint()  # 运行到这里会进入 pdb 调试器
#
# pdb 常用命令：
# n (next)     → 下一行
# s (step)     → 进入函数
# c (continue) → 继续运行
# p variable   → 打印变量
# l (list)     → 显示当前代码
# q (quit)     → 退出

# --- 11. 性能分析 ---
python3 -m timeit -s "d={i:i for i in range(1000)}" "d[500]"
python3 -m cProfile -s cumulative script.py  # 按累计时间排序
python3 -m cProfile -o output.prof script.py # 输出到文件
python3 -m pstats output.prof                # 交互式查看

# --- 12. 创建可执行 zip 应用 ---
# 把整个项目打包成一个可直接运行的 .pyz 文件：
python3 -m zipapp myapp -o myapp.pyz -p "/usr/bin/env python3"
# myapp/ 目录下需要有 __main__.py
python3 myapp.pyz  # 直接运行
chmod +x myapp.pyz && ./myapp.pyz  # 加执行权限后直接运行
"""

# ============================================================
# 五、项目结构最佳实践
# ============================================================

"""
# 一个标准的 Python 项目长这样：
my_project/
├── pyproject.toml        # 项目元数据 + 构建配置（现代标准）
├── requirements.txt      # 或者用 pyproject.toml 的 dependencies
├── src/
│   └── my_package/
│       ├── __init__.py
│       ├── core.py
│       └── utils.py
├── tests/
│   ├── __init__.py
│   └── test_core.py
├── .venv/                # 虚拟环境（不要提交到 git）
└── README.md

# --- pyproject.toml 最小示例 ---
# [project]
# name = "my-package"
# version = "0.1.0"
# requires-python = ">=3.10"
# dependencies = [
#     "requests>=2.28",
#     "click>=8.0",
# ]
#
# [project.optional-dependencies]
# dev = ["pytest", "ruff"]
#
# [project.scripts]
# my-tool = "my_package.core:main"   # 安装后生成 my-tool 命令

# --- .gitignore 中应该包含 ---
# .venv/
# __pycache__/
# *.pyc
# *.egg-info/
# dist/
# build/
"""

# ============================================================
# 六、常见问题排查
# ============================================================

"""
# 问题1: pip 和 python3 版本不匹配
# 症状: pip install 了但 import 找不到
# 原因: pip 对应的是另一个 python
# 解决: 永远用 python3 -m pip install xxx

# 问题2: Permission denied
# 不要用 sudo pip install！
# 解决: 用虚拟环境，或 pip install --user

# 问题3: 包安装了但 import 报错
python3 -c "import sys; print(sys.path)"  # 看搜索路径
pip show package_name  # 看装到了哪里
# 确认 pip 和 python3 是同一个环境的

# 问题4: 虚拟环境激活后 python3 还是系统的
hash -r              # 清除 bash 的命令缓存
which python3        # 确认路径
deactivate && source myenv/bin/activate  # 重新激活

# 问题5: 依赖冲突
pip check            # 检查
pip install --force-reinstall package  # 强制重装

# 问题6: 想看某个包的源码
pip show -f requests | grep Location   # 找到安装位置
# 然后直接去那个目录读源码
"""

# ============================================================
# 七、可运行的演示代码
# ============================================================

import sys
import subprocess


def demo():
    print("=== 当前 Python 环境信息 ===")
    print(f"  版本: {sys.version}")
    print(f"  路径: {sys.executable}")
    print(f"  前缀: {sys.prefix}")
    print(f"  在虚拟环境中? {sys.prefix != sys.base_prefix}")

    print(f"\n=== sys.path（包搜索路径）===")
    sys.path.insert(1, "/home/iaa/Code/git")
    for p in sys.path:
        print(f"  {p}")

    print(f"\n=== 已安装的包数量 ===")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=columns"],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split("\n")
        print(f"  共 {len(lines) - 2} 个包")
        print("  前5个:")
        for line in lines[2:7]:
            print(f"    {line}")
    except Exception as e:
        print(f"  无法获取: {e}")

    print(f"\n=== 实用一行命令演示 ===")
    demos = [
        ("UUID", [sys.executable, "-c", "import uuid; print(uuid.uuid4())"]),
        ("Python之禅(前3行)", [sys.executable, "-c",
         "import this"]),
    ]
    for name, cmd in demos[:1]:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"  {name}: {result.stdout.strip()}")


if __name__ == "__main__":
    demo()
