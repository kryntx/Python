"""
10 - 元类简介
运行方式: python 10_metaclass.py

元类是"创建类的类"。type 是所有类的默认元类。
日常开发很少需要写元类，但理解它有助于读懂框架源码（ORM、序列化库等）。
"""

# ============================================================
# 1. 类也是对象
# ============================================================

class Foo:
    pass

# Foo 本身是 type 的实例
print(type(Foo))    # <class 'type'>
print(type(int))    # <class 'type'>
print(type(type))   # <class 'type'>（type 是自己的元类）

# 可以动态创建类（等价于 class 语句）
Bar = type("Bar", (object,), {"x": 42, "greet": lambda self: "hi"})
b = Bar()
print(b.x)       # 42
print(b.greet()) # hi


# ============================================================
# 2. 元类的工作机制
# ============================================================
# 创建类时，Python 调用: metaclass(name, bases, namespace)
# 默认 metaclass = type

class MetaExample(type):
    """最简单的元类：打印类创建过程"""

    def __new__(mcs, name, bases, namespace):
        print(f"  [元类] 正在创建类: {name}")
        print(f"  [元类] 基类: {bases}")
        print(f"  [元类] 属性: {[k for k in namespace if not k.startswith('__')]}")
        cls = super().__new__(mcs, name, bases, namespace)
        return cls


class MyClass(metaclass=MetaExample):
    x = 1
    def method(self):
        pass

# 输出:
#   [元类] 正在创建类: MyClass
#   [元类] 基类: (<class 'object'>,)
#   [元类] 属性: ['x', 'method']


# ============================================================
# 3. 实用元类：自动注册所有子类
# ============================================================

class PluginMeta(type):
    """自动把子类注册到 plugins 字典"""
    plugins = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        # 跳过基类本身
        if bases:
            key = name.lower().replace("plugin", "")
            mcs.plugins[key] = cls
            print(f"  注册插件: {key} -> {name}")
        return cls


class BasePlugin(metaclass=PluginMeta):
    def run(self):
        raise NotImplementedError


class CompressPlugin(BasePlugin):
    def run(self):
        return "压缩中..."

class EncryptPlugin(BasePlugin):
    def run(self):
        return "加密中..."

class UploadPlugin(BasePlugin):
    def run(self):
        return "上传中..."

print(f"\n已注册: {list(PluginMeta.plugins.keys())}")
# 已注册: ['compress', 'encrypt', 'upload']

# 通过名字动态创建插件
plugin_cls = PluginMeta.plugins["compress"]
print(plugin_cls().run())  # 压缩中...


# ============================================================
# 4. 实用元类：接口检查（强制子类实现方法）
# ============================================================

class InterfaceMeta(type):
    """确保子类实现了所有必需方法"""
    required_methods = ()

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:  # 跳过基类
            missing = [
                m for m in mcs.required_methods
                if not callable(getattr(cls, m, None))
            ]
            if missing:
                raise TypeError(
                    f"类 {name} 缺少必需方法: {', '.join(missing)}"
                )
        return cls


class Service(metaclass=InterfaceMeta):
    required_methods = ("start", "stop", "health_check")


# 这样会报错：
# class BadService(Service):
#     def start(self): pass
# TypeError: 类 BadService 缺少必需方法: stop, health_check

class GoodService(Service):
    def start(self):
        return "started"
    def stop(self):
        return "stopped"
    def health_check(self):
        return "ok"

print(f"\nGoodService 创建成功: {GoodService().health_check()}")


# ============================================================
# 5. __init_subclass__：轻量替代（不需要元类）
# ============================================================
# Python 3.6+ 很多场景不需要完整元类

class Validated:
    """子类定义时自动检查字段"""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # 检查子类是否定义了 required_fields
        required = getattr(cls, "required_fields", [])
        annotations = getattr(cls, "__annotations__", {})
        missing = [f for f in required if f not in annotations]
        if missing:
            raise TypeError(f"{cls.__name__} 缺少字段声明: {missing}")
        print(f"  验证通过: {cls.__name__}")


class UserForm(Validated):
    required_fields = ["name", "email"]
    name: str
    email: str
    age: int = 0  # 可选字段

# 验证通过: UserForm

# 这样会报错：
# class BadForm(Validated):
#     required_fields = ["name", "email"]
#     name: str
# TypeError: BadForm 缺少字段声明: ['email']


# ============================================================
# 6. 描述符（Descriptor）：property 的底层机制
# ============================================================
# 实现了 __get__, __set__, __delete__ 的对象就是描述符

class ValidatedField:
    """通用字段校验描述符"""

    def __init__(self, min_value=None, max_value=None):
        self.min_value = min_value
        self.max_value = max_value

    def __set_name__(self, owner, name):
        # Python 3.6+：自动获取属性名
        self.name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.name, None)

    def __set__(self, obj, value):
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"{self.name} 不能小于 {self.min_value}")
        if self.max_value is not None and value > self.max_value:
            raise ValueError(f"{self.name} 不能大于 {self.max_value}")
        setattr(obj, self.name, value)


class Product:
    price = ValidatedField(min_value=0)
    quantity = ValidatedField(min_value=0, max_value=10000)

    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price        # 触发 ValidatedField.__set__
        self.quantity = quantity


prod = Product("键盘", 299, 50)
print(f"价格: {prod.price}, 数量: {prod.quantity}")

try:
    prod.price = -10
except ValueError as e:
    print(f"错误: {e}")  # _price 不能小于 0


# ============================================================
# 7. 总结：什么时候用什么
# ============================================================
# 需求                          用什么
# 简单的属性校验/计算           -> @property
# 类创建时做检查/注册           -> __init_subclass__
# 可复用的属性校验逻辑          -> 描述符
# 需要控制类的创建过程          -> 元类
# 强制接口（抽象方法）          -> ABC（比元类更 Pythonic）


# ============================================================
# 练习：
# 1. 写一个元类，自动给所有方法添加计时功能
# 2. 用描述符实现一个 TypedField，确保属性类型正确
# 3. 用 __init_subclass__ 实现一个简单的"模型"基类，
#    自动收集子类定义的字段名
# ============================================================

if __name__ == "__main__":
    print("\n--- 练习参考: 自动收集字段 ---")

    class Model:
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            cls._fields = list(getattr(cls, "__annotations__", {}).keys())

        def __init__(self, **kwargs):
            for field_name in self._fields:
                setattr(self, field_name, kwargs.get(field_name))

        def to_dict(self):
            return {f: getattr(self, f, None) for f in self._fields}

    class Article(Model):
        title: str
        content: str
        views: int

    a = Article(title="Python元类", content="...", views=100)
    print(f"  字段: {Article._fields}")
    print(f"  数据: {a.to_dict()}")
