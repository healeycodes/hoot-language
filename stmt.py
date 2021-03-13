from abc import ABCMeta, abstractmethod
from tokens import Token
from typing import List


class StmtVisitor(metaclass=ABCMeta):
    @abstractmethod
    def visit_block_stmt(self, stmt): pass

    @abstractmethod
    def visit_break_stmt(self, stmt): pass

    @abstractmethod
    def visit_class_stmt(self, stmt): pass

    @abstractmethod
    def visit_expression_stmt(self, stmt): pass

    @abstractmethod
    def visit_function_stmt(self, stmt): pass

    @abstractmethod
    def visit_if_stmt(self, stmt): pass

    @abstractmethod
    def visit_print_stmt(self, stmt): pass

    @abstractmethod
    def visit_return_stmt(self, stmt): pass

    @abstractmethod
    def visit_var_stmt(self, stmt): pass

    @abstractmethod
    def visit_while_stmt(self, stmt): pass


class Stmt(metaclass=ABCMeta):
    @abstractmethod
    def accept(self, visitor): pass


class Block(Stmt):
    def __init__(self, statements: List[Stmt], block_type=None):
        self.statements = statements
        self.block_type = block_type

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_block_stmt(self)


class Class(Stmt):
    def __init__(self, name: Token, superclass, methods: List):
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_class_stmt(self)


class Expression(Stmt):
    def __init__(self, expression):
        self.expression = expression

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_expression_stmt(self)


class Function(Stmt):
    def __init__(self, name: Token, params: List[Token], body: List[Stmt]):
        self.name = name
        self.params = params
        self.body = body

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_function_stmt(self)


class If(Stmt):
    def __init__(self, condition, then_branch, else_branch):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_if_stmt(self)


class Print(Stmt):
    def __init__(self, expression):
        self.expression = expression

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_print_stmt(self)


class Return(Stmt):
    def __init__(self, keyword: Token, value):
        self.keyword = keyword
        self.value = value

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_return_stmt(self)


class Let(Stmt):
    def __init__(self, name, initializer):
        self.name = name
        self.initializer = initializer

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_var_stmt(self)


class While(Stmt):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def accept(self, visitor: StmtVisitor):
        return visitor.visit_while_stmt(self)


class Break(Stmt):
    def accept(self, visitor: StmtVisitor):
        return visitor.visit_break_stmt(self)
