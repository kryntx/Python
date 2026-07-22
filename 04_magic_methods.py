"""
04 - 魔术方法（dunder methods）
运行方式: python 04_magic_methods.py
"""

# ============================================================
# 1. 字符串表示：__str__ vs __repr__
# ============================================================

class Color:
    def __init__(self, r, g, b):
        self.r, self.g, self.b = r, g, b

    def __repr__(self):
        # 给开发者看：精确、可复制粘贴重建对象
        return f"Color({self.r}, {self.g}, {self.b})"

    def __str__(self):
        # 给用户看：友好
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"


c = Color(255, 128, 0)
print(c)        # #ff8000（调用 __str__）
print(repr(c))  # Color(255, 128, 0)（调用 __repr__）
# 在交互式解释器中直接输入 c，显示的是 repr


# ============================================================
# 2. 比较运算：__eq__, __lt__, __gt__ 等
# ============================================================
# 用 functools.total_ordering 只需定义 __eq__ 和一个比较方法

from functools import total_ordering


@total_ordering
class Version:
    def __init__(self, major, minor, patch=0):
        self.major = major
        self.minor = minor
        self.patch = patch

    def _tuple(self):
        return (self.major, self.minor, self.patch)

    def __eq__(self, other):
        return self._tuple() == other._tuple()

    def __lt__(self, other):
        return self._tuple() < other._tuple()

    def __repr__(self):
        return f"Version({self.major}.{self.minor}.{self.patch})"


v1 = Version(1, 2, 3)
v2 = Version(1, 3, 0)
print(v1 < v2)   # True
print(v1 >= v2)  # False（total_ordering 自动推导）
print(v1 == Version(1, 2, 3))  # True


# ============================================================
# 3. 算术运算：__add__, __sub__, __mul__ 等
# ============================================================

class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar):
        """向量 * 标量"""
        return Vector(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar):
        """标量 * 向量（反向乘法）"""
        return self.__mul__(scalar)

    def __abs__(self):
        """abs(v) 返回模长"""
        return (self.x ** 2 + self.y ** 2) ** 0.5

    def __repr__(self):
        return f"Vector({self.x}, {self.y})"


a = Vector(3, 4)
b = Vector(1, 2)
print(a + b)       # Vector(4, 6)
print(a - b)       # Vector(2, 2)
print(a * 3)       # Vector(9, 12)
print(2 * a)       # Vector(6, 8)（触发 __rmul__）
print(abs(a))      # 5.0


# ============================================================
# 4. 容器协议：__len__, __getitem__, __setitem__, __contains__
# ============================================================

class Playlist:
    def __init__(self, name):
        self.name = name
        self._songs = []

    def add(self, song):
        self._songs.append(song)

    def __len__(self):
        return len(self._songs)

    def __getitem__(self, index):
        """支持 pl[0], pl[1:3], for song in pl"""
        return self._songs[index]

    def __setitem__(self, index, song):
        self._songs[index] = song

    def __contains__(self, song):
        """支持 'song' in pl"""
        return song in self._songs

    def __repr__(self):
        return f"Playlist('{self.name}', {len(self)} songs)"


pl = Playlist("工作BGM")
pl.add("Song A")
pl.add("Song B")
pl.add("Song C")

print(len(pl))        # 3
print(pl[0])          # Song A
print(pl[1:3])        # ['Song B', 'Song C']（切片也能用）
print("Song B" in pl) # True

for song in pl:       # 可迭代（__getitem__ 从0开始依次调用直到 IndexError）
    print(f"  播放: {song}")


# ============================================================
# 5. 可调用对象：__call__
# ============================================================

class Multiplier:
    """让实例像函数一样被调用"""

    def __init__(self, factor):
        self.factor = factor

    def __call__(self, x):
        return x * self.factor


double = Multiplier(2)
triple = Multiplier(3)
print(double(5))   # 10
print(triple(5))   # 15
print(callable(double))  # True


# 实用场景：带状态的回调
class Counter:
    def __init__(self):
        self.count = 0

    def __call__(self):
        self.count += 1
        return self.count


counter = Counter()
print(counter())  # 1
print(counter())  # 2
print(counter())  # 3


# ============================================================
# 6. __bool__ 和真值测试
# ============================================================

class SearchResults:
    def __init__(self, items):
        self.items = items

    def __bool__(self):
        """空结果为 False"""
        return len(self.items) > 0

    def __len__(self):
        return len(self.items)


results = SearchResults([])
if not results:
    print("没有找到结果")  # 会执行

results2 = SearchResults(["a", "b"])
if results2:
    print(f"找到 {len(results2)} 条结果")  # 找到 2 条结果


# ============================================================
# 7. __hash__：让对象可以作为字典的 key / 放入 set
# ============================================================
# 规则：如果 a == b，则 hash(a) == hash(b)

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


p1 = Point(1, 2)
p2 = Point(1, 2)
p3 = Point(3, 4)

# 可以放入 set 去重
points = {p1, p2, p3}
print(points)  # {Point(1, 2), Point(3, 4)}（p1 和 p2 相等，去重）

# 可以作为字典 key
locations = {p1: "起点", p3: "终点"}
print(locations[p2])  # "起点"（p2 == p1，所以能查到）


# ============================================================
# 练习：
# 实现一个 Matrix 类（2x2），支持 +, *, ==, repr
# 实现 __getitem__ 让 m[0][1] 能访问元素
# ============================================================
