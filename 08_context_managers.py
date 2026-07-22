"""
08 - 上下文管理器
运行方式: python 08_context_managers.py
"""

import time
import os

# ============================================================
# 1. with 语句的本质
# ============================================================
# with 语句确保"进入时获取资源，退出时释放资源"
# 即使发生异常也能正确清理

# 你已经在用的：
# with open("file.txt") as f:    <- __enter__ 打开文件
#     data = f.read()
#                                  <- __exit__ 关闭文件（即使出错）


# ============================================================
# 2. 用类实现上下文管理器：__enter__ + __exit__
# ============================================================

class Timer:
    """计时上下文管理器"""

    def __enter__(self):
        self.start = time.perf_counter()
        return self  # 返回值赋给 as 后面的变量

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start
        print(f"  耗时: {self.elapsed:.4f}s")
        # 返回 False/None：异常继续传播
        # 返回 True：吞掉异常（一般别这么做）
        return False


with Timer() as t:
    time.sleep(0.1)
    # 模拟工作
print(f"  记录的时间: {t.elapsed:.4f}s")  # 可以在 with 外访问


class ManagedResource:
    """展示 __exit__ 处理异常的能力"""

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        print(f"  获取资源: {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"  释放资源: {self.name}")
        if exc_type:
            print(f"  捕获到异常: {exc_type.__name__}: {exc_val}")
            return True  # 吞掉异常，with 块外不会报错
        return False


with ManagedResource("DB连接"):
    print("  使用中...")
    raise ValueError("模拟错误")
# 输出:
#   获取资源: DB连接
#   使用中...
#   释放资源: DB连接
#   捕获到异常: ValueError: 模拟错误
print("  程序继续执行（异常被吞掉了）")


# ============================================================
# 3. 用 contextmanager 装饰器（更简洁）
# ============================================================

from contextlib import contextmanager


@contextmanager
def temp_directory(prefix="tmp_"):
    """创建临时目录，用完自动删除"""
    import tempfile, shutil
    path = tempfile.mkdtemp(prefix=prefix)
    print(f"  创建临时目录: {path}")
    try:
        yield path  # yield 之前 = __enter__，yield 的值 = as 的变量
    finally:
        shutil.rmtree(path)  # yield 之后 = __exit__（finally 确保执行）
        print(f"  已删除: {path}")


with temp_directory() as tmpdir:
    test_file = os.path.join(tmpdir, "test.txt")
    with open(test_file, "w") as f:
        f.write("hello")
    print(f"  文件存在: {os.path.exists(test_file)}")
# with 结束后目录已被删除


@contextmanager
def suppress_exceptions(*exceptions):
    """抑制指定类型的异常"""
    try:
        yield
    except exceptions as e:
        print(f"  已抑制: {type(e).__name__}: {e}")


with suppress_exceptions(FileNotFoundError, PermissionError):
    open("/nonexistent/path/file.txt")
print("  继续执行")


# ============================================================
# 4. 实用上下文管理器集合
# ============================================================

# --- 工作目录切换 ---
@contextmanager
def cd(path):
    """临时切换工作目录"""
    old_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)


print(f"\n当前目录: {os.getcwd()}")
with cd("/tmp"):
    print(f"切换后: {os.getcwd()}")
print(f"恢复后: {os.getcwd()}")


# --- 环境变量临时修改 ---
@contextmanager
def env(**kwargs):
    """临时设置环境变量"""
    old_values = {}
    for key, value in kwargs.items():
        old_values[key] = os.environ.get(key)
        os.environ[key] = value
    try:
        yield
    finally:
        for key, old_value in old_values.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


with env(MY_VAR="test_value", DEBUG="1"):
    print(f"\nMY_VAR = {os.environ['MY_VAR']}")  # test_value
    print(f"DEBUG = {os.environ['DEBUG']}")       # 1
print(f"MY_VAR 存在? {'MY_VAR' in os.environ}")   # False


# --- 简单的锁/互斥 ---
import threading

class LockContext:
    """线程锁的上下文管理器"""

    def __init__(self):
        self._lock = threading.Lock()

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, *args):
        self._lock.release()


lock = LockContext()
with lock:
    print("\n临界区：同一时间只有一个线程能进入")


# ============================================================
# 5. ExitStack：动态管理多个上下文管理器
# ============================================================

from contextlib import ExitStack

# 场景：不确定要打开多少个文件
filenames = ["/tmp/f1.txt", "/tmp/f2.txt", "/tmp/f3.txt"]

with ExitStack() as stack:
    files = []
    for name in filenames:
        f = stack.enter_context(open(name, "w"))
        files.append(f)

    for i, f in enumerate(files):
        f.write(f"content {i}")

# 所有文件在这里都已自动关闭
print(f"\n文件都已关闭: {all(f.closed for f in files)}")

# 清理测试文件
for name in filenames:
    os.remove(name)


# ============================================================
# 6. 异步上下文管理器（预览）
# ============================================================
# async with 使用 __aenter__ / __aexit__

# class AsyncConnection:
#     async def __aenter__(self):
#         await self.connect()
#         return self
#
#     async def __aexit__(self, *args):
#         await self.disconnect()
#
# async with AsyncConnection() as conn:
#     await conn.query("SELECT 1")


# ============================================================
# 练习：
# 1. 写一个 AtomicWrite 上下文管理器：先写临时文件，成功后 rename
#    （防止写一半崩溃导致文件损坏）
# 2. 写一个 @contextmanager 实现数据库事务（成功 commit，异常 rollback）
# ============================================================

if __name__ == "__main__":
    print("\n--- 练习参考: AtomicWrite ---")

    @contextmanager
    def atomic_write(filepath, mode="w"):
        tmp_path = filepath + ".tmp"
        f = open(tmp_path, mode)
        try:
            yield f
            f.close()
            os.replace(tmp_path, filepath)  # 原子操作
            print(f"  写入成功: {filepath}")
        except Exception:
            f.close()
            os.remove(tmp_path)
            print(f"  写入失败，已回滚")
            raise

    with atomic_write("/tmp/atomic_test.txt") as f:
        f.write("safe content")

    with open("/tmp/atomic_test.txt") as f:
        print(f"  内容: {f.read()}")

    os.remove("/tmp/atomic_test.txt")
