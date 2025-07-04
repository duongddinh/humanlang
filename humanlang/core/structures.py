
class TypeSystemError(Exception): pass
class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value

class Environment:
    def __init__(self, outer=None):
        self.outer = outer
        self.values = {}
        self.types = {}

    def get(self, name):
        if name in self.values: return self.values[name]
        if self.outer: return self.outer.get(name)
        return None

    def get_type(self, name):
        if name in self.types: return self.types[name]
        if self.outer: return self.outer.get_type(name)
        return "any"

    def set(self, name, value, var_type="any"):
        self.values[name] = value
        if var_type != "any": self.types[name] = var_type

    def declare(self, name, var_type):
        if name in self.types: raise TypeSystemError(f"Variable '{name}' has already been declared.")
        self.types[name] = var_type
    def update(self, name, value):
        if name in self.values:
            self.values[name] = value
            return True
        if self.outer:
            return self.outer.update(name, value)
        return False


class ClassDefinition:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.methods = {}
        self.properties = {}

    def find_method(self, name):
        if name in self.methods: return self.methods[name]
        if self.parent: return self.parent.find_method(name)
        return None

class ObjectInstance:
    def __init__(self, class_def):
        self.class_def = class_def
        self.env = Environment()
