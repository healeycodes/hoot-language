from abc import ABCMeta, abstractmethod
from stmt import Function
from environment import Environment
from tokens import Token
from typing import Dict, List


class ReturnBubble(Exception):
    def __init__(self, value):
        self.value = value


class HootCallable(metaclass=ABCMeta):
    @abstractmethod
    def call(self, interpreter, arguments: List, error_token: Token): pass

    @abstractmethod
    def arity(self, interpreter, arguments: List): pass


class HootInstance:
    def __init__(self, klass):
        self.klass = klass
        self.fields = {}

    def get(self, name: Token):
        if name.lexeme in self.fields:
            return self.fields[name.lexeme]

        method = self.klass.find_method(name.lexeme)
        if method != None:
            return method.bind(self)
        raise RuntimeError(name, f"Undefined property '{name.lexeme}'.")

    def set_(self, name: Token, value):
        self.fields[name.lexeme] = value

    def __repr__(self):
        return f"{self.klass.name} instance"


class HootClass(HootCallable):
    def __init__(self, name, superclass, methods: Dict):
        self.superclass = superclass
        self.name = name
        self.methods = methods

    def find_method(self, name: str):
        if name in self.methods:
            return self.methods[name]
        if self.superclass != None:
            return self.superclass.find_method(name)

    def call(self, interpreter, arguments: List, error_token: Token):
        instance = HootInstance(self)
        initializer = self.find_method("init")
        if initializer != None:
            initializer.bind(instance).call(
                interpreter, arguments, error_token)
        return instance

    def arity(self, interpreter, arguments):
        initializer = self.find_method("init")
        if initializer == None:
            return 0
        return initializer.arity(interpreter, arguments)

    def __repr__(self):
        return self.name


class HootFunction(HootCallable):
    def __init__(self, declaration: Function, closure: Environment, is_initializer: bool):
        self.declaration = declaration
        self.closure = closure
        self.is_initializer = is_initializer

    def bind(self, instance: HootInstance):
        environment = Environment(self.closure)
        environment.define("this", instance)
        return HootFunction(self.declaration, environment, self.is_initializer)

    def arity(self, interpreter, arguments):
        return len(self.declaration.params)

    def call(self, interpreter, arguments: List, error_token: Token):
        environment = Environment(self.closure)
        for idx, param in enumerate(self.declaration.params):
            environment.define(param.lexeme, arguments[idx])

        try:
            interpreter.execute_block(self.declaration.body, environment)
        except ReturnBubble as return_value:
            if self.is_initializer:
                return self.closure.get_at(0, "this")
            return return_value.value

        if self.is_initializer:
            return self.closure.get_at(0, "this")

    def __repr__(self):
        return f"<fn {self.declaration.name.lexeme}>"
