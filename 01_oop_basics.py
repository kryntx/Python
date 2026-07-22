"""
01 - OOP基础：类、实例、属性、方法
运行方式: python 01_oop_basics.py
"""

# ============================================================
# 1. 定义类与创建实例
# ============================================================

class Task:
    """一个待办事项"""

    # 类属性：所有实例共享
    count = 0

    def __init__(self, title, priority="medium"):
        # 实例属性：每个实例独有
        self.title = title
        self.priority = priority
        self.done = False
        Task.count += 1  # 每创建一个实例，计数+1

    # 实例方法：第一个参数必须是 self（代表实例本身）
    def complete(self):
        self.done = True
        print(f"[完成] {self.title}")

    def __str__(self):
        status = "x" if self.done else " "
        return f"[{status}] {self.title} (优先级: {self.priority})"


# 创建实例
t1 = Task("学习Python OOP", priority="high")
t2 = Task("写周报")

print(t1)          # [ ] 学习Python OOP (优先级: high)
print(t2)          # [ ] 写周报 (优先级: medium)
t1.complete()      # [完成] 学习Python OOP
print(t1)          # [x] 学习Python OOP (优先级: high)
print(f"共创建 {Task.count} 个任务")  # 共创建 2 个任务


# ============================================================
# 2. 类属性 vs 实例属性
# ============================================================

class Config:
    app_name = "MyApp"  # 类属性，所有实例共享

    def __init__(self, env):
        self.env = env  # 实例属性

c1 = Config("dev")
c2 = Config("prod")

print(c1.app_name)  # MyApp（从类属性读取）
print(c2.app_name)  # MyApp

# 通过实例修改类属性？不会！只会创建同名的实例属性
c1.app_name = "DevApp"
print(c1.app_name)  # DevApp（实例属性，遮蔽了类属性）
print(c2.app_name)  # MyApp（不受影响）
print(Config.app_name)  # MyApp（类属性本身没变）


# ============================================================
# 3. self 到底是什么？
# ============================================================

class Counter:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1
        return self  # 返回 self 支持链式调用

    def show(self):
        print(f"当前值: {self.value}")
        return self


c = Counter()
# 下面两种写法完全等价：
c.increment()          # Python 自动把 c 传给 self
Counter.increment(c)   # 手动传 self

# 链式调用（因为方法返回了 self）
c.increment().increment().show()  # 当前值: 3


# ============================================================
# 4. __init__ 不是"构造函数"，而是"初始化器"
# ============================================================
# 真正创建实例的是 __new__，__init__ 只是给已创建的实例赋初始值
# 绝大多数情况只需要写 __init__

class Point:
    def __new__(cls, *args, **kwargs):
        print(f"__new__ 被调用，创建 {cls.__name__} 实例")
        return super().__new__(cls)  # 必须返回一个实例

    def __init__(self, x, y):
        print(f"__init__ 被调用，初始化 ({x}, {y})")
        self.x = x
        self.y = y


p = Point(3, 4)
# 输出:
# __new__ 被调用，创建 Point 实例
# __init__ 被调用，初始化 (3, 4)


# ============================================================
# 5. 实用技巧：用 __slots__ 限制属性、节省内存
# ============================================================

class SlotPoint:
    __slots__ = ("x", "y")  # 只允许这两个属性

    def __init__(self, x, y):
        self.x = x
        self.y = y


sp = SlotPoint(1, 2)
print(sp.x, sp.y)  # 1 2

try:
    sp.z = 3  # 报错！不允许添加未声明的属性
except AttributeError as e:
    print(f"AttributeError: {e}")


# ============================================================
# 练习：
# 创建一个 FileItem 类，有 name, size(字节), modified(字符串) 属性
# 实现一个 human_size() 方法，把字节转为 KB/MB 显示
# 实现 __str__ 让 print 输出友好格式
# ============================================================

if __name__ == "__main__":
    print("\n--- 练习参考 ---")

    class FileItem:
        def __init__(self, name, size, modified):
            self.name = name
            self.size = size
            self.modified = modified

        def human_size(self):
            if self.size >= 1024 * 1024:
                return f"{self.size / 1024 / 1024:.1f} MB"
            elif self.size >= 1024:
                return f"{self.size / 1024:.1f} KB"
            return f"{self.size} B"

        def __str__(self):
            return f"{self.name:<20} {self.human_size():>10}  {self.modified}"

    f = FileItem("report.pdf", 2_500_000, "2026-07-20")
    print(f)  # report.pdf              2.4 MB  2026-07-20
