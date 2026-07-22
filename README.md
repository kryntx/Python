# Python 面向对象与高级特性教程

从 OOP 基础到元类，配合工具/脚本方向的实战项目，边看边跑的学习路径。

## 环境要求

- Python 3.10+
- 无第三方依赖，标准库即可运行

```bash
python3 --version  # 确认版本
```

## 目录结构

```
├── 00_toolchain.py                    # 工具链：venv、pip、python 命令及隐藏技巧
├── 01_oop_basics.py                   # 类、实例、属性、方法、__slots__
├── 02_inheritance.py                  # 继承、多态、MRO、Mixin、组合优于继承
├── 03_encapsulation.py                # 封装、property、__getattr__/__setattr__
├── 04_magic_methods.py                # dunder methods：比较、算术、容器协议、__call__
├── 05_classmethod_staticmethod_abc.py # 类方法、静态方法、抽象基类、Protocol
├── 06_decorators.py                   # 函数/类装饰器、带参装饰器、实用装饰器集
├── 07_iterators_generators.py         # 迭代器协议、yield、管道式处理、send()
├── 08_context_managers.py             # with 原理、contextmanager、ExitStack
├── 09_dataclass_typehints.py          # dataclass、类型提示、Enum
├── 10_metaclass.py                    # 元类、描述符、__init_subclass__
├── file_organizer.py                  # 实战：CLI 文件整理工具
├── config_manager.py                  # 实战：多层级配置管理器
└── log_analyzer.py                    # 实战：日志分析器
```

## 快速开始

```bash
# 建议创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 按顺序阅读运行
python3 00_toolchain.py
python3 01_oop_basics.py
python3 02_inheritance.py
# ... 依次类推
```

## 学习路径

| 阶段 | 章节 | 核心内容 |
|------|------|----------|
| 入门 | 00 | 熟悉 python3/pip/venv 命令 |
| 基础 | 01-03 | 类与实例、继承多态、封装与 property |
| 进阶 | 04-06 | 魔术方法、抽象类、装饰器 |
| 高级 | 07-10 | 生成器、上下文管理器、dataclass、元类 |
| 实战 | 3个项目 | 综合运用以上知识点 |

## 实战项目

### file_organizer.py — CLI 文件整理工具

按文件类型自动归类到子目录，支持多种策略和预览模式。

```bash
python3 file_organizer.py /path/to/messy/folder --dry-run
python3 file_organizer.py . --strategy extension
```

涉及：dataclass、Enum、ABC、策略模式、argparse、pathlib

### config_manager.py — 配置管理器

支持多层级配置、环境变量覆盖、临时修改、类型校验。

```bash
python3 config_manager.py
```

涉及：描述符、`__getattr__`、上下文管理器、单例、装饰器

### log_analyzer.py — 日志分析器

解析多格式日志、可组合过滤器、统计报告生成。

```bash
python3 log_analyzer.py              # 自动生成示例日志并分析
python3 log_analyzer.py app.log      # 分析指定文件
```

涉及：生成器管道、正则、dataclass、运算符重载组合过滤器

## 说明

- 每个文件独立可运行，无需按顺序依赖
- 每章末尾附有练习题，部分提供了参考答案
- 代码注释为中文，适合中文读者
