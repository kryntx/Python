"""
02 - 继承与多态
运行方式: python 02_inheritance.py
"""

# ============================================================
# 1. 基本继承
# ============================================================

class BaseOutput:
    """输出基类"""

    def __init__(self, prefix=""):
        self.prefix = prefix

    def write(self, msg):
        print(f"{self.prefix}{msg}")

    def flush(self):
        pass  # 基类默认什么都不做


class FileOutput(BaseOutput):
    """写入文件的输出（这里用 print 模拟）"""

    def __init__(self, filename, prefix=""):
        super().__init__(prefix)  # 调用父类 __init__
        self.filename = filename
        self._buffer = []

    def write(self, msg):
        # 重写父类方法
        self._buffer.append(f"{self.prefix}{msg}")

    def flush(self):
        # 模拟写入文件
        content = "\n".join(self._buffer)
        print(f"[写入 {self.filename}]\n{content}")
        self._buffer.clear()


class ConsoleOutput(BaseOutput):
    """控制台输出，带颜色标记"""

    def write(self, msg):
        print(f"\033[36m{self.prefix}{msg}\033[0m")  # 青色


# 多态：同一个接口，不同行为
outputs = [
    ConsoleOutput(prefix="[INFO] "),
    FileOutput("app.log", prefix="[LOG] "),
]

for out in outputs:
    out.write("程序启动")  # 各自调用自己的 write
    out.flush()           # ConsoleOutput 什么都不做，FileOutput 输出缓冲


# ============================================================
# 2. 多重继承与 MRO（方法解析顺序）
# ============================================================

class Logger:
    def log(self, msg):
        print(f"[LOG] {msg}")


class Timer:
    def log(self, msg):
        print(f"[TIMER] {msg}")


# Python 用 C3 线性化算法决定 MRO
class TimedLogger(Logger, Timer):
    pass


tl = TimedLogger()
tl.log("hello")  # [LOG] hello（Logger 在前，优先）

# 查看 MRO
print(TimedLogger.__mro__)
# (<class TimedLogger>, <class Logger>, <class Timer>, <class object>)


# ============================================================
# 3. Mixin 模式：用多重继承组合功能
# ============================================================

import json
import time


class JsonMixin:
    """给任何类添加 JSON 序列化能力"""

    def to_json(self):
        # 只序列化实例属性（不以 _ 开头的）
        data = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}
        return json.dumps(data, ensure_ascii=False, indent=2)


class TimestampMixin:
    """给任何类添加创建时间"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # 协作式调用，保证 MRO 链不断
        self.created_at = time.strftime("%Y-%m-%d %H:%M:%S")


class ServerConfig(TimestampMixin, JsonMixin):
    def __init__(self, host, port):
        super().__init__()  # 触发 TimestampMixin.__init__
        self.host = host
        self.port = port


cfg = ServerConfig("localhost", 8080)
print(cfg.created_at)  # 2026-07-22 xx:xx:xx
print(cfg.to_json())
# {
#   "created_at": "...",
#   "host": "localhost",
#   "port": 8080
# }


# ============================================================
# 4. super() 的正确理解
# ============================================================
# super() 不是"调用父类"，而是"调用 MRO 中的下一个类"

class A:
    def greet(self):
        print("A")
        super().greet() if hasattr(super(), "greet") else None


class B(A):
    def greet(self):
        print("B")
        super().greet()


class C(A):
    def greet(self):
        print("C")
        super().greet()


class D(B, C):
    def greet(self):
        print("D")
        super().greet()


D().greet()
# 输出: D -> B -> C -> A
# 这就是 MRO 链：D -> B -> C -> A -> object


# ============================================================
# 5. 组合优于继承（实用建议）
# ============================================================
# 当关系不是 "is-a" 而是 "has-a" 时，用组合

class Formatter:
    def format(self, text):
        return text.upper()


class Reporter:
    def __init__(self, formatter=None):
        # 组合：持有 formatter 的引用，而非继承它
        self.formatter = formatter or Formatter()

    def report(self, text):
        return self.formatter.format(text)


r = Reporter()
print(r.report("hello world"))  # HELLO WORLD

# 可以轻松替换策略
class MarkdownFormatter:
    def format(self, text):
        return f"**{text}**"

r2 = Reporter(MarkdownFormatter())
print(r2.report("hello"))  # **hello**


# ============================================================
# 练习：
# 创建一个 Shape 基类（有 area() 和 perimeter() 方法）
# 派生 Circle, Rectangle, Triangle
# 写一个函数 total_area(shapes: list) 计算总面积（利用多态）
# ============================================================

if __name__ == "__main__":
    import math

    class Shape:
        def area(self):
            raise NotImplementedError

        def perimeter(self):
            raise NotImplementedError

    class Circle(Shape):
        def __init__(self, r):
            self.r = r

        def area(self):
            return math.pi * self.r ** 2

        def perimeter(self):
            return 2 * math.pi * self.r

    class Rectangle(Shape):
        def __init__(self, w, h):
            self.w = w
            self.h = h

        def area(self):
            return self.w * self.h

        def perimeter(self):
            return 2 * (self.w + self.h)

    def total_area(shapes):
        return sum(s.area() for s in shapes)

    shapes = [Circle(5), Rectangle(3, 4)]
    print(f"\n总面积: {total_area(shapes):.2f}")  # 90.54
