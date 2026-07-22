"""
03 - 封装与 property
运行方式: python 03_encapsulation.py
"""

# ============================================================
# 1. Python 的"封装"是约定，不是强制
# ============================================================

class Account:
    def __init__(self, owner, balance=0):
        self.owner = owner       # 公开属性
        self._balance = balance  # 单下划线：约定"内部使用"，外部别碰
        self.__secret = "x"     # 双下划线：名称改写（name mangling）


acc = Account("Alice", 1000)
print(acc.owner)       # Alice
print(acc._balance)    # 1000（能访问，但不应该）

# 双下划线被改写为 _类名__属性名
# print(acc.__secret)  # AttributeError!
print(acc._Account__secret)  # x（强行访问，但别这么干）


# ============================================================
# 2. @property：把方法调用伪装成属性访问
# ============================================================

class Temperature:
    def __init__(self, celsius=0):
        self._celsius = celsius  # 内部存储用摄氏度

    @property
    def celsius(self):
        """读取时触发"""
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        """赋值时触发，可以做校验"""
        if value < -273.15:
            raise ValueError("温度不能低于绝对零度")
        self._celsius = value

    @property
    def fahrenheit(self):
        """只读属性：没有 setter"""
        return self._celsius * 9 / 5 + 32

    @property
    def kelvin(self):
        return self._celsius + 273.15


t = Temperature(100)
print(t.celsius)      # 100（像属性一样读取，实际调用了 getter）
print(t.fahrenheit)   # 212.0
print(t.kelvin)       # 373.15

t.celsius = 25        # 触发 setter
print(t.fahrenheit)   # 77.0

try:
    t.celsius = -300  # 触发校验
except ValueError as e:
    print(f"错误: {e}")  # 温度不能低于绝对零度

# t.fahrenheit = 100  # AttributeError: 没有 setter，只读


# ============================================================
# 3. 用 property 实现延迟计算（缓存）
# ============================================================

import time


class DataReport:
    def __init__(self, data):
        self._data = data
        self._cache = {}

    @property
    def total(self):
        if "total" not in self._cache:
            print("  (计算 total 中...)")
            time.sleep(0.1)  # 模拟耗时计算
            self._cache["total"] = sum(self._data)
        return self._cache["total"]

    @property
    def average(self):
        if "average" not in self._cache:
            print("  (计算 average 中...)")
            self._cache["average"] = self.total / len(self._data)
        return self._cache["average"]

    def invalidate(self):
        """数据变了就清缓存"""
        self._cache.clear()


report = DataReport([10, 20, 30, 40])
print(report.total)    # (计算 total 中...) 100
print(report.total)    # 100（命中缓存，不再计算）
print(report.average)  # (计算 average 中...) 25.0


# ============================================================
# 4. 用 property 实现只读/受控的容器属性
# ============================================================

class TaskList:
    def __init__(self):
        self._tasks = []

    @property
    def tasks(self):
        """返回副本，防止外部直接修改内部列表"""
        return list(self._tasks)

    @property
    def count(self):
        return len(self._tasks)

    def add(self, task):
        if not task.strip():
            raise ValueError("任务不能为空")
        self._tasks.append(task.strip())

    def remove(self, index):
        return self._tasks.pop(index)


tl = TaskList()
tl.add("学习 property")
tl.add("写代码")
print(tl.tasks)   # ['学习 property', '写代码']
print(tl.count)   # 2

# 外部拿到的是副本，修改不影响内部
fake = tl.tasks
fake.append("hack")
print(tl.count)   # 仍然是 2


# ============================================================
# 5. __getattr__ / __setattr__：更底层的属性控制
# ============================================================

class DotDict:
    """让字典支持点号访问: d.key 等价于 d['key']"""

    def __init__(self, data=None):
        # 注意：必须用 object.__setattr__ 避免递归
        object.__setattr__(self, "_data", data or {})

    def __getattr__(self, name):
        # 只在常规查找失败时触发
        data = object.__getattribute__(self, "_data")
        if name in data:
            return data[name]
        raise AttributeError(f"没有属性 '{name}'")

    def __setattr__(self, name, value):
        self._data[name] = value

    def __repr__(self):
        return f"DotDict({self._data})"


d = DotDict({"host": "localhost", "port": 8080})
print(d.host)      # localhost
print(d.port)      # 8080
d.debug = True     # 通过 __setattr__ 写入
print(d)           # DotDict({'host': 'localhost', 'port': 8080, 'debug': True})


# ============================================================
# 练习：
# 创建一个 ValidatedAge 类，用 property 确保 age 在 0-150 之间
# 再创建一个 ReadOnlyList，外部只能读取不能修改
# ============================================================

if __name__ == "__main__":
    class ValidatedAge:
        def __init__(self, age=0):
            self.age = age  # 触发 setter

        @property
        def age(self):
            return self._age

        @age.setter
        def age(self, value):
            if not isinstance(value, int):
                raise TypeError("年龄必须是整数")
            if not 0 <= value <= 150:
                raise ValueError("年龄必须在 0-150 之间")
            self._age = value

    person = ValidatedAge(25)
    print(f"\n年龄: {person.age}")
    try:
        person.age = 200
    except ValueError as e:
        print(f"错误: {e}")
