"""
07 - 迭代器与生成器
运行方式: python 07_iterators_generators.py
"""

# ============================================================
# 1. 可迭代对象 vs 迭代器
# ============================================================
# 可迭代对象(Iterable)：实现了 __iter__，如 list, str, dict
# 迭代器(Iterator)：实现了 __iter__ + __next__，每次调用 next() 返回下一个值

lst = [1, 2, 3]       # 可迭代对象
it = iter(lst)        # 获取迭代器
print(next(it))       # 1
print(next(it))       # 2
print(next(it))       # 3
# next(it)            # StopIteration 异常（没有更多元素）


# ============================================================
# 2. 自定义迭代器：实现 __iter__ + __next__
# ============================================================

class Countdown:
    """从 n 倒数到 1"""

    def __init__(self, n):
        self.n = n

    def __iter__(self):
        # 返回一个迭代器（这里返回自身）
        self.current = self.n
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value


for num in Countdown(5):
    print(num, end=" ")  # 5 4 3 2 1
print()


# 更好的做法：__iter__ 返回生成器（见下文），避免状态污染
# 上面的实现只能遍历一次，因为状态存在实例上


# ============================================================
# 3. 生成器函数：用 yield 简化迭代器
# ============================================================

def countdown(n):
    """yield 版本——自动处理 StopIteration"""
    while n > 0:
        yield n  # 暂停并返回值，下次 next() 从这里继续
        n -= 1


for num in countdown(5):
    print(num, end=" ")  # 5 4 3 2 1
print()

# 生成器是惰性的：不会一次性生成所有值
g = countdown(3)
print(type(g))     # <class 'generator'>
print(next(g))     # 3
print(next(g))     # 2
print(next(g))     # 1


# ============================================================
# 4. 生成器的实用场景
# ============================================================

# --- 读取大文件（不一次性加载到内存）---
def read_chunks(filepath, chunk_size=1024):
    """逐块读取文件"""
    with open(filepath, "r") as f:
        while chunk := f.read(chunk_size):
            yield chunk


# --- 无限序列 ---
def fibonacci():
    """无限斐波那契数列"""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


# 取前 10 个
from itertools import islice
print(list(islice(fibonacci(), 10)))
# [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


# --- 管道式数据处理 ---
def filter_errors(lines):
    for line in lines:
        if "ERROR" in line:
            yield line

def extract_message(lines):
    for line in lines:
        # 假设格式: "2026-07-22 ERROR: something went wrong"
        yield line.split("ERROR: ", 1)[-1].strip()

def take(n, iterable):
    for i, item in enumerate(iterable):
        if i >= n:
            break
        yield item


# 模拟日志
fake_logs = [
    "2026-07-22 INFO: started",
    "2026-07-22 ERROR: disk full",
    "2026-07-22 INFO: retrying",
    "2026-07-22 ERROR: timeout",
    "2026-07-22 ERROR: connection lost",
]

# 管道：filter -> extract -> take
pipeline = take(2, extract_message(filter_errors(fake_logs)))
for msg in pipeline:
    print(f"  错误: {msg}")
# 错误: disk full
# 错误: timeout


# ============================================================
# 5. yield from：委托给子生成器
# ============================================================

def flatten(nested):
    """展平嵌套列表"""
    for item in nested:
        if isinstance(item, list):
            yield from flatten(item)  # 等价于 for x in flatten(item): yield x
        else:
            yield item


data = [1, [2, 3, [4, 5]], 6, [7, [8]]]
print(list(flatten(data)))  # [1, 2, 3, 4, 5, 6, 7, 8]


# ============================================================
# 6. 生成器表达式 vs 列表推导式
# ============================================================

# 列表推导：立即计算，占用内存
squares_list = [x**2 for x in range(1000000)]  # 占 ~8MB

# 生成器表达式：惰性计算，几乎不占内存
squares_gen = (x**2 for x in range(1000000))   # 只是一个生成器对象

# 用于 sum/max/any 等聚合函数时，生成器表达式更高效
total = sum(x**2 for x in range(1000000))  # 不需要额外列表
print(f"平方和: {total}")


# ============================================================
# 7. 生成器的 send() 和协程基础
# ============================================================

def accumulator():
    """可以接收外部数据的生成器"""
    total = 0
    while True:
        value = yield total  # yield 返回 total，同时接收 send() 的值
        if value is None:
            break
        total += value


acc = accumulator()
next(acc)            # 启动生成器（必须先 next 一次）
print(acc.send(10))  # 10
print(acc.send(20))  # 30
print(acc.send(5))   # 35


# ============================================================
# 8. 实用：用生成器实现文件 tail -f 效果
# ============================================================

import os

def tail_lines(filepath, n=5):
    """读取文件最后 n 行（不用读整个文件）"""
    with open(filepath, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        lines = []
        pos = size

        while pos > 0 and len(lines) <= n:
            pos = max(0, pos - 1024)
            f.seek(pos)
            chunk = f.read(min(1024, size - pos))
            lines = chunk.decode().splitlines() + lines

    return lines[-n:]


# 创建测试文件
test_file = "/tmp/tail_test.txt"
with open(test_file, "w") as f:
    for i in range(20):
        f.write(f"line {i}\n")

print("\n最后3行:")
for line in tail_lines(test_file, 3):
    print(f"  {line}")


# ============================================================
# 练习：
# 1. 写一个生成器 prime_numbers()，无限产出素数
# 2. 写一个 chain_generators(*iterables) 把多个可迭代对象串联
# 3. 用生成器实现一个简单的"事件流"处理器
# ============================================================

if __name__ == "__main__":
    print("\n--- 练习参考: 素数生成器 ---")

    def prime_numbers():
        """埃拉托斯特尼筛法的生成器版本"""
        yield 2
        candidates = 3
        found = [2]
        while True:
            is_prime = all(candidates % p != 0 for p in found if p <= candidates**0.5)
            if is_prime:
                found.append(candidates)
                yield candidates
            candidates += 2

    print(list(islice(prime_numbers(), 15)))
    # [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
