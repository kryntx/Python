"""
09 - dataclass 与类型提示
运行方式: python 09_dataclass_typehints.py
"""

from dataclasses import dataclass, field, asdict, astuple
from typing import Optional
from enum import Enum

# ============================================================
# 1. 没有 dataclass 时的痛点
# ============================================================

# 传统写法：大量样板代码
class OldPoint:
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"OldPoint(x={self.x}, y={self.y}, z={self.z})"

    def __eq__(self, other):
        return (self.x, self.y, self.z) == (other.x, other.y, other.z)


# ============================================================
# 2. dataclass：自动生成 __init__, __repr__, __eq__ 等
# ============================================================

@dataclass
class Point:
    x: float
    y: float
    z: float = 0.0  # 带默认值的字段必须放在后面


p1 = Point(1.0, 2.0)
p2 = Point(1.0, 2.0, 0.0)
print(p1)         # Point(x=1.0, y=2.0, z=0.0)
print(p1 == p2)   # True（自动生成 __eq__）
print(p1.x)       # 1.0


# ============================================================
# 3. 常用参数
# ============================================================

# frozen=True：不可变（类似 namedtuple）
@dataclass(frozen=True)
class Config:
    host: str
    port: int
    debug: bool = False


cfg = Config("localhost", 8080)
print(cfg)  # Config(host='localhost', port=8080, debug=False)
# cfg.port = 9090  # FrozenInstanceError! 不能修改

# frozen 的 dataclass 自动有 __hash__，可以放入 set/dict
configs = {cfg}
print(f"可哈希: {hash(cfg) is not None}")


# order=True：自动生成比较方法
@dataclass(order=True)
class Priority:
    level: int
    name: str = field(compare=False)  # compare=False：不参与比较


tasks = [Priority(3, "low"), Priority(1, "urgent"), Priority(2, "normal")]
for t in sorted(tasks):
    print(f"  {t.level}: {t.name}")
# 1: urgent
# 2: normal
# 3: low


# ============================================================
# 4. field() 的高级用法
# ============================================================

@dataclass
class Project:
    name: str
    tags: list = field(default_factory=list)  # 可变默认值必须用 factory
    metadata: dict = field(default_factory=dict)
    _id: int = field(init=False, repr=False, default=0)  # 不作为构造参数

    def __post_init__(self):
        """__init__ 之后自动调用，做额外初始化"""
        self._id = id(self) % 10000  # 模拟生成 ID


proj = Project("my-app", tags=["python", "cli"])
print(proj)          # Project(name='my-app', tags=['python', 'cli'], metadata={})
print(proj._id)      # 某个数字（repr 中不显示）

# 注意：不能用 tags: list = []，所有实例会共享同一个列表！


# ============================================================
# 5. dataclass 的转换工具
# ============================================================

@dataclass
class User:
    name: str
    age: int
    email: Optional[str] = None


user = User("Alice", 30, "alice@example.com")

# 转为字典
print(asdict(user))
# {'name': 'Alice', 'age': 30, 'email': 'alice@example.com'}

# 转为元组
print(astuple(user))
# ('Alice', 30, 'alice@example.com')


# ============================================================
# 6. 类型提示（Type Hints）基础
# ============================================================
# 类型提示不影响运行，但能让 IDE 和 mypy 帮你检查错误

def greet(name: str) -> str:
    return f"Hello, {name}"

def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("除数不能为0")
    return a / b

# 变量注解
count: int = 0
name: str = "Python"
scores: list[int] = [90, 85, 92]
mapping: dict[str, int] = {"a": 1, "b": 2}


# ============================================================
# 7. 常用类型提示
# ============================================================

from typing import Union

# Optional[X] 等价于 Union[X, None]
def find_user(user_id: int) -> Optional[User]:
    if user_id == 1:
        return User("Alice", 30)
    return None

# Union：多种类型
def process(data: Union[str, bytes]) -> str:
    if isinstance(data, bytes):
        return data.decode()
    return data

# Python 3.10+ 可以用 | 代替 Union
# def process(data: str | bytes) -> str: ...

# Callable：函数类型
from typing import Callable

def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

print(apply(lambda x, y: x + y, 3, 4))  # 7

# TypeVar：泛型
from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T:
    return items[0]

# IDE 能推断出 first([1,2,3]) 返回 int，first(["a","b"]) 返回 str


# ============================================================
# 8. Enum + dataclass 组合
# ============================================================

class Status(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Job:
    name: str
    status: Status = Status.PENDING
    retries: int = 0

    def start(self):
        self.status = Status.RUNNING

    def finish(self, success=True):
        self.status = Status.DONE if success else Status.FAILED


job = Job("数据导出")
print(job)  # Job(name='数据导出', status=<Status.PENDING: 'pending'>, retries=0)
job.start()
print(job.status)  # Status.RUNNING
job.finish()
print(job.status.value)  # done


# ============================================================
# 9. 嵌套 dataclass 与序列化
# ============================================================

import json

@dataclass
class Address:
    city: str
    street: str

@dataclass
class Employee:
    name: str
    age: int
    address: Address
    skills: list[str] = field(default_factory=list)


emp = Employee(
    name="Bob",
    age=28,
    address=Address("北京", "长安街1号"),
    skills=["Python", "SQL"],
)

# asdict 会递归转换嵌套 dataclass
emp_dict = asdict(emp)
print(json.dumps(emp_dict, ensure_ascii=False, indent=2))

# 从字典重建
emp2 = Employee(**{**emp_dict, "address": Address(**emp_dict["address"])})
print(emp2 == emp)  # True


# ============================================================
# 练习：
# 1. 用 @dataclass(frozen=True, order=True) 实现一个 Version 类
# 2. 给下面的函数加上完整的类型提示：
#    def merge_dicts(d1, d2): ...
#    def retry(func, times, delay): ...
# ============================================================

if __name__ == "__main__":
    print("\n--- 练习参考 ---")

    @dataclass(frozen=True, order=True)
    class SemVer:
        major: int
        minor: int
        patch: int

        def __str__(self):
            return f"{self.major}.{self.minor}.{self.patch}"

    versions = [SemVer(1, 2, 0), SemVer(1, 0, 1), SemVer(2, 0, 0), SemVer(1, 2, 1)]
    for v in sorted(versions):
        print(f"  v{v}")

    def merge_dicts(d1: dict[str, int], d2: dict[str, int]) -> dict[str, int]:
        return {**d1, **d2}

    def retry(
        func: Callable[[], T],
        times: int = 3,
        delay: float = 0.1,
    ) -> T:
        for attempt in range(times):
            try:
                return func()
            except Exception:
                if attempt == times - 1:
                    raise
                time.sleep(delay)
        raise RuntimeError("unreachable")
