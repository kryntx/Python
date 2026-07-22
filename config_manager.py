"""
实战2 - 配置管理器
运行方式: python examples/config_manager.py

综合运用: 描述符, __getattr__, 上下文管理器, 装饰器, 单例, 类型提示
功能: 支持多层级配置、环境变量覆盖、类型校验、临时修改
"""

import json
import os
from pathlib import Path
from typing import Any, Optional
from contextlib import contextmanager


# ============================================================
# 类型校验描述符
# ============================================================

class TypedConfigValue:
    """确保配置值类型正确的描述符"""

    def __init__(self, expected_type: type, default: Any = None):
        self.expected_type = expected_type
        self.default = default
        self.name = ""

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj._data.get(self.name, self.default)

    def __set__(self, obj, value):
        if value is not None and not isinstance(value, self.expected_type):
            raise TypeError(
                f"配置项 '{self.name}' 期望 {self.expected_type.__name__}，"
                f"得到 {type(value).__name__}"
            )
        obj._data[self.name] = value


# ============================================================
# 核心：ConfigNode（树形配置节点）
# ============================================================

class ConfigNode:
    """
    支持点号访问的嵌套配置:
        config.database.host
        config.database.port
    """

    def __init__(self, data: Optional[dict] = None):
        object.__setattr__(self, "_data", data or {})

    def __getattr__(self, name: str) -> Any:
        data = object.__getattribute__(self, "_data")
        if name not in data:
            raise KeyError(f"配置项不存在: '{name}'")
        value = data[name]
        # 嵌套字典自动转为 ConfigNode
        if isinstance(value, dict):
            return ConfigNode(value)
        return value

    def __setattr__(self, name: str, value: Any):
        self._data[name] = value

    def __contains__(self, name: str) -> bool:
        return name in self._data

    def __repr__(self) -> str:
        return f"ConfigNode({json.dumps(self._data, ensure_ascii=False, indent=2)})"

    def get(self, key: str, default: Any = None) -> Any:
        """安全获取，支持点号路径: config.get('database.host')"""
        keys = key.split(".")
        current = self._data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        if isinstance(current, dict):
            return ConfigNode(current)
        return current

    def set(self, key: str, value: Any):
        """设置值，支持点号路径，自动创建中间层级"""
        keys = key.split(".")
        current = self._data
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

    def to_dict(self) -> dict:
        return dict(self._data)

    def merge(self, other: dict):
        """深度合并另一个字典"""
        self._deep_merge(self._data, other)

    @staticmethod
    def _deep_merge(base: dict, override: dict):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigNode._deep_merge(base[key], value)
            else:
                base[key] = value


# ============================================================
# 配置管理器（单例 + 多来源）
# ============================================================

class ConfigManager:
    """
    配置优先级（高到低）:
    1. 环境变量 (APP_DATABASE__HOST=xxx)
    2. 运行时修改
    3. 配置文件
    4. 默认值
    """

    _instance: Optional["ConfigManager"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, env_prefix: str = "APP"):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._env_prefix = env_prefix
        self._config = ConfigNode()
        self._defaults = ConfigNode()
        self._history: list[tuple[str, Any, Any]] = []  # (key, old, new)

    @classmethod
    def reset(cls):
        """重置单例（测试用）"""
        cls._instance = None

    def load_file(self, path: str | Path):
        """从 JSON 文件加载配置"""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"配置文件不存在: {path}")
        with open(path) as f:
            data = json.load(f)
        self._config.merge(data)
        print(f"已加载配置: {path}")

    def load_dict(self, data: dict):
        """从字典加载"""
        self._config.merge(data)

    def set_defaults(self, data: dict):
        """设置默认值"""
        self._defaults.merge(data)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值（按优先级查找）"""
        # 1. 环境变量
        env_key = f"{self._env_prefix}_{key.upper().replace('.', '__')}"
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return self._convert_type(env_value, key)

        # 2. 运行时配置
        value = self._config.get(key)
        if value is not None:
            return value

        # 3. 默认值
        value = self._defaults.get(key)
        if value is not None:
            return value

        return default

    def set(self, key: str, value: Any):
        """运行时修改配置（记录历史）"""
        old = self.get(key)
        self._history.append((key, old, value))
        self._config.set(key, value)

    @contextmanager
    def override(self, **kwargs):
        """临时覆盖配置，退出后恢复"""
        old_values = {}
        for key, value in kwargs.items():
            old_values[key] = self.get(key)
            self.set(key, value)
        try:
            yield self
        finally:
            for key, old_value in old_values.items():
                self._config.set(key, old_value)

    def _convert_type(self, value: str, key: str) -> Any:
        """环境变量都是字符串，尝试转换类型"""
        # 先看当前配置中该 key 的类型
        current = self._config.get(key)
        if isinstance(current, bool):
            return value.lower() in ("1", "true", "yes")
        if isinstance(current, int):
            return int(value)
        if isinstance(current, float):
            return float(value)
        return value

    def __repr__(self):
        return f"ConfigManager(prefix={self._env_prefix}, keys={list(self._config._data.keys())})"


# ============================================================
# 装饰器：注入配置
# ============================================================

def with_config(*keys: str):
    """把配置值注入函数参数"""
    def decorator(func):
        import functools

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cfg = ConfigManager()
            for key in keys:
                param_name = key.replace(".", "_")
                if param_name not in kwargs:
                    kwargs[param_name] = cfg.get(key)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# 演示
# ============================================================

def main():
    ConfigManager.reset()
    cfg = ConfigManager(env_prefix="MYAPP")

    # 设置默认值
    cfg.set_defaults({
        "database": {"host": "localhost", "port": 5432, "name": "mydb"},
        "cache": {"ttl": 300, "backend": "memory"},
        "debug": False,
    })

    # 加载配置文件（模拟）
    cfg.load_dict({
        "database": {"host": "192.168.1.100", "port": 5432},
        "cache": {"backend": "redis"},
    })

    print("=== 基本读取 ===")
    print(f"  database.host = {cfg.get('database.host')}")   # 192.168.1.100
    print(f"  database.port = {cfg.get('database.port')}")   # 5432
    print(f"  database.name = {cfg.get('database.name')}")   # mydb（来自默认值）
    print(f"  cache.backend = {cfg.get('cache.backend')}")   # redis
    print(f"  cache.ttl     = {cfg.get('cache.ttl')}")       # 300（来自默认值）
    print(f"  debug         = {cfg.get('debug')}")           # False

    print("\n=== 环境变量覆盖 ===")
    os.environ["MYAPP_DATABASE__HOST"] = "prod-server.com"
    os.environ["MYAPP_DEBUG"] = "true"
    print(f"  database.host = {cfg.get('database.host')}")   # prod-server.com
    print(f"  debug         = {cfg.get('debug')}")           # True（字符串转bool）
    del os.environ["MYAPP_DATABASE__HOST"]
    del os.environ["MYAPP_DEBUG"]

    print("\n=== 临时覆盖（上下文管理器）===")
    print(f"  覆盖前: cache.ttl = {cfg.get('cache.ttl')}")
    with cfg.override(**{"cache.ttl": 60}):
        print(f"  覆盖中: cache.ttl = {cfg.get('cache.ttl')}")  # 60
    print(f"  覆盖后: cache.ttl = {cfg.get('cache.ttl')}")  # 300（恢复）

    print("\n=== 运行时修改 ===")
    cfg.set("database.port", 3306)
    print(f"  database.port = {cfg.get('database.port')}")  # 3306

    print("\n=== 使用装饰器注入配置 ===")

    @with_config("database.host", "database.port")
    def connect(database_host=None, database_port=None):
        print(f"  连接到 {database_host}:{database_port}")

    connect()  # 自动从配置读取

    print("\n=== ConfigNode 点号访问 ===")
    node = ConfigNode({"server": {"host": "0.0.0.0", "port": 8080}})
    print(f"  {node.server.host}:{node.server.port}")


if __name__ == "__main__":
    main()
