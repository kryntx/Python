"""
06 - 装饰器（函数装饰器与类装饰器）
运行方式: python 06_decorators.py
"""

import time
import functools

# ============================================================
# 1. 函数是一等公民——装饰器的基础
# ============================================================

def greet(name):
    return f"Hello, {name}"

# 函数可以赋值给变量
say = greet
print(say("World"))  # Hello, World

# 函数可以作为参数传递
def apply(func, arg):
    return func(arg)

print(apply(greet, "Python"))  # Hello, Python


# ============================================================
# 2. 最简单的装饰器
# ============================================================

def timer(func):
    """测量函数执行时间"""
    @functools.wraps(func)  # 保留原函数的 __name__, __doc__
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  [{func.__name__}] 耗时 {elapsed:.4f}s")
        return result
    return wrapper


@timer  # 等价于 slow_add = timer(slow_add)
def slow_add(a, b):
    """两数相加（模拟慢操作）"""
    time.sleep(0.1)
    return a + b


result = slow_add(3, 4)
print(f"结果: {result}")        # 结果: 7
print(slow_add.__name__)        # slow_add（因为 @wraps）
print(slow_add.__doc__)         # 两数相加（模拟慢操作）


# ============================================================
# 3. 带参数的装饰器（三层嵌套）
# ============================================================

def retry(max_attempts=3, delay=0.1):
    """失败自动重试"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        print(f"  [{func.__name__}] 第{attempt}次尝试失败，放弃: {e}")
                        raise
                    print(f"  [{func.__name__}] 第{attempt}次失败，{delay}s后重试...")
                    time.sleep(delay)
        return wrapper
    return decorator


call_count = 0

@retry(max_attempts=3, delay=0.05)
def unstable_api():
    """模拟不稳定的API"""
    global call_count
    call_count += 1
    if call_count < 3:
        raise ConnectionError("网络超时")
    return "success"


print(unstable_api())  # 第1次失败... 第2次失败... success


# ============================================================
# 4. 用类实现装饰器（带状态）
# ============================================================

class CallCounter:
    """记录函数被调用的次数"""

    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"  [{self.func.__name__}] 第 {self.count} 次调用")
        return self.func(*args, **kwargs)


@CallCounter
def process(data):
    return data.strip().lower()


print(process("  Hello "))   # hello（第 1 次调用）
print(process(" WORLD "))    # world（第 2 次调用）
print(process.count)         # 2


# ============================================================
# 5. 实用装饰器集合
# ============================================================

# --- 缓存（记忆化）---
def memoize(func):
    cache = {}
    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    wrapper.cache = cache
    return wrapper


@memoize
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


print(f"\nfib(30) = {fib(30)}")  # 瞬间完成（无缓存会非常慢）
print(f"缓存条目数: {len(fib.cache)}")


# --- 参数校验 ---
def validate_types(**type_hints):
    """运行时类型检查"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for name, expected_type in type_hints.items():
                value = bound.arguments[name]
                if not isinstance(value, expected_type):
                    raise TypeError(
                        f"参数 '{name}' 期望 {expected_type.__name__}，"
                        f"实际得到 {type(value).__name__}"
                    )
            return func(*args, **kwargs)
        return wrapper
    return decorator


@validate_types(name=str, age=int)
def create_user(name, age):
    return {"name": name, "age": age}


print(create_user("Alice", 30))  # {'name': 'Alice', 'age': 30}
try:
    create_user("Bob", "thirty")
except TypeError as e:
    print(f"TypeError: {e}")


# --- 废弃警告 ---
def deprecated(reason=""):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import warnings
            msg = f"{func.__name__} 已废弃" + (f": {reason}" if reason else "")
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator


@deprecated("请使用 new_connect()")
def old_connect():
    return "connected"


import warnings
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    old_connect()
    print(f"\n警告: {w[0].message}")  # old_connect 已废弃: 请使用 new_connect()


# ============================================================
# 6. 类装饰器：装饰一个类
# ============================================================

def add_repr(cls):
    """自动给类添加 __repr__"""
    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{cls.__name__}({attrs})"
    cls.__repr__ = __repr__
    return cls


@add_repr
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email


u = User("Alice", "alice@example.com")
print(u)  # User(name='Alice', email='alice@example.com')


# 更实用：自动注册所有子类
def auto_register(cls):
    """把子类自动注册到 registry"""
    if not hasattr(cls, "registry"):
        cls.registry = {}

    original_init_subclass = cls.__init_subclass__

    @classmethod
    def __init_subclass__(kls, **kwargs):
        super(cls, kls).__init_subclass__(**kwargs)
        cls.registry[kls.__name__] = kls

    cls.__init_subclass__ = __init_subclass__
    return cls


@auto_register
class Handler:
    registry = {}


class JsonHandler(Handler):
    pass

class XmlHandler(Handler):
    pass

print(f"\n已注册的 Handler: {list(Handler.registry.keys())}")
# 已注册的 Handler: ['JsonHandler', 'XmlHandler']


# ============================================================
# 练习：
# 1. 写一个 @log_calls 装饰器，打印函数的参数和返回值
# 2. 写一个 @singleton 装饰器，确保类只有一个实例
# 3. 写一个 @rate_limit(calls=5, period=1) 限制调用频率
# ============================================================

if __name__ == "__main__":
    print("\n--- 练习参考: singleton ---")

    def singleton(cls):
        instances = {}
        @functools.wraps(cls)
        def get_instance(*args, **kwargs):
            if cls not in instances:
                instances[cls] = cls(*args, **kwargs)
            return instances[cls]
        return get_instance

    @singleton
    class Database:
        def __init__(self):
            print("  创建数据库连接")

    db1 = Database()  # 创建数据库连接
    db2 = Database()  # 不会再打印
    print(f"  同一个实例? {db1 is db2}")  # True
