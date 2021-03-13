from tokens import Token
from error import RuntimeError


class Environment:
    def __init__(self, enclosing):
        self.enclosing = enclosing
        self.values = {}

    def define(self, name, value):
        self.values[name] = value

    def ancestor(self, distance: int):
        environment = self
        for _ in range(0, distance):
            environment = environment.enclosing
        return environment

    def get_at(self, distance: int, name: str):
        return self.ancestor(distance).values.get(name)

    def assign_at(self, distance: int, name: Token, value):
        self.ancestor(distance).values[name.lexeme] = value

    def get(self, name):
        if name.lexeme in self.values:
            return self.values[name.lexeme]
        if self.enclosing != None:
            return self.enclosing.get(name)
        raise RuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def assign(self, name, value):
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self.enclosing != None:
            self.enclosing.assign(name, value)
            return
        raise RuntimeError(name, f"Undefined variable '{name.lexeme}'.")
