"""
05 - 类方法、静态方法、抽象类
运行方式: python 05_classmethod_staticmethod_abc.py
"""

# ============================================================
# 1. @classmethod：操作类本身，而非实例
# ============================================================

class Date:
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day

    @classmethod
    def from_string(cls, s):
        """工厂方法：从字符串创建实例"""
        year, month, day = map(int, s.split("-"))
        return cls(year, month, day)  # cls 是类本身，子类继承时也能正确工作

    @classmethod
    def today(cls):
        """工厂方法：创建今天的日期"""
        import time
        t = time.localtime()
        return cls(t.tm_year, t.tm_mon, t.tm_mday)

    def __repr__(self):
        return f"Date({self.year}, {self.month}, {self.day})"


d1 = Date.from_string("2026-07-22")
d2 = Date.today()
print(d1)  # Date(2026, 7, 22)
print(d2)  # Date(2026, 7, 22)


# classmethod 在继承中的优势
class DateTime(Date):
    def __init__(self, year, month, day, hour=0, minute=0):
        super().__init__(year, month, day)
        self.hour = hour
        self.minute = minute


# from_string 用的是 cls(...)，所以子类调用时 cls=DateTime
dt = DateTime.from_string("2026-01-01")
print(type(dt))  # <class 'DateTime'>（不是 Date！）


# ============================================================
# 2. @staticmethod：不依赖类或实例的纯工具函数
# ============================================================

class MathUtils:
    @staticmethod
    def gcd(a, b):
        """最大公约数（不需要 self 或 cls）"""
        while b:
            a, b = b, a % b
        return a

    @staticmethod
    def is_prime(n):
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True


print(MathUtils.gcd(12, 8))    # 4
print(MathUtils.is_prime(17))  # True

# 实例也能调用，但没意义（访问不到实例数据）
m = MathUtils()
print(m.gcd(100, 75))  # 25


# ============================================================
# 3. 对比总结
# ============================================================
# 方法类型        第一个参数    能访问什么          典型用途
# 实例方法        self       实例+类             操作实例数据
# @classmethod   cls        类（不能访问实例）    工厂方法、操作类属性
# @staticmethod  无         都不能              工具函数、逻辑分组


# ============================================================
# 4. 抽象基类（ABC）：定义接口契约
# ============================================================

from abc import ABC, abstractmethod


class Storage(ABC):
    """存储后端接口——不能直接实例化"""

    @abstractmethod
    def save(self, key, value):
        """保存数据"""
        ...

    @abstractmethod
    def load(self, key):
        """读取数据"""
        ...

    @abstractmethod
    def delete(self, key):
        """删除数据"""
        ...

    # 可以有具体方法（模板方法）
    def save_many(self, items: dict):
        for k, v in items.items():
            self.save(k, v)


# s = Storage()  # TypeError: 不能实例化抽象类！


class MemoryStorage(Storage):
    def __init__(self):
        self._data = {}

    def save(self, key, value):
        self._data[key] = value

    def load(self, key):
        return self._data.get(key)

    def delete(self, key):
        self._data.pop(key, None)


class FileStorage(Storage):
    def __init__(self, directory="/tmp/storage"):
        self.directory = directory

    def save(self, key, value):
        import os, json
        os.makedirs(self.directory, exist_ok=True)
        path = os.path.join(self.directory, f"{key}.json")
        with open(path, "w") as f:
            json.dump(value, f)

    def load(self, key):
        import os, json
        path = os.path.join(self.directory, f"{key}.json")
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return json.load(f)

    def delete(self, key):
        import os
        path = os.path.join(self.directory, f"{key}.json")
        if os.path.exists(path):
            os.remove(path)


# 多态使用
def demo_storage(storage: Storage):
    storage.save("name", "Python")
    storage.save_many({"version": 3.12, "year": 2026})
    print(f"  name = {storage.load('name')}")
    print(f"  version = {storage.load('version')}")
    storage.delete("name")
    print(f"  name after delete = {storage.load('name')}")


print("\n--- MemoryStorage ---")
demo_storage(MemoryStorage())

print("\n--- FileStorage ---")
demo_storage(FileStorage())


# ============================================================
# 5. 用 ABC 做插件系统
# ============================================================

class Plugin(ABC):
    name: str  # 子类必须定义

    @abstractmethod
    def execute(self, data):
        ...


class UpperPlugin(Plugin):
    name = "upper"

    def execute(self, data):
        return data.upper()


class ReversePlugin(Plugin):
    name = "reverse"

    def execute(self, data):
        return data[::-1]


# 插件注册表
PLUGINS: dict[str, Plugin] = {}

def register(plugin_cls):
    p = plugin_cls()
    PLUGINS[p.name] = p

register(UpperPlugin)
register(ReversePlugin)

# 使用
text = "hello world"
for name, plugin in PLUGINS.items():
    print(f"  {name}: {plugin.execute(text)}")
# upper: HELLO WORLD
# reverse: dlrow olleh


# ============================================================
# 6. Protocol（鸭子类型的类型检查，Python 3.8+）
# ============================================================
# 不需要继承，只要"长得像"就行

from typing import Protocol, runtime_checkable


@runtime_checkable
class Renderable(Protocol):
    def render(self) -> str:
        ...


class Button:
    def render(self) -> str:
        return "<button>Click</button>"


class Text:
    def render(self) -> str:
        return "<p>Hello</p>"


def draw(widget: Renderable):
    print(widget.render())


draw(Button())  # <button>Click</button>
draw(Text())    # <p>Hello</p>

# runtime_checkable 允许 isinstance 检查
print(isinstance(Button(), Renderable))  # True


# ============================================================
# 练习：
# 1. 给 Date 类加一个 from_timestamp(ts) 类方法
# 2. 创建一个抽象类 Exporter（有 export 方法），实现 CsvExporter 和 JsonExporter
# ============================================================
