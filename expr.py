from abc import ABCMeta, abstractmethod
from tokens import Token
from typing import List, Union


class ExprVisitor(metaclass=ABCMeta):
    @abstractmethod
    def visit_assign_expr(self, expr): pass

    @abstractmethod
    def visit_binary_expr(self, expr): pass

    @abstractmethod
    def visit_call_expr(self, expr): pass

    @abstractmethod
    def visit_grouping_expr(self, expr): pass

    @abstractmethod
    def visit_get_expr(self, expr): pass

    @abstractmethod
    def visit_literal_expr(self, expr): pass

    @abstractmethod
    def visit_logical_expr(self, expr): pass

    @abstractmethod
    def visit_set_expr(self, expr): pass

    @abstractmethod
    def visit_super_expr(self, expr): pass

    @abstractmethod
    def visit_this_expr(self, expr): pass

    @abstractmethod
    def visit_unary_expr(self, expr): pass

    @abstractmethod
    def visit_variable_expr(self, expr): pass


class Expr(metaclass=ABCMeta):
    @abstractmethod
    def accept(self, visitor: ExprVisitor): pass


class Assign(Expr):
    def __init__(self, name: Token, value: Expr):
        self.name = name
        self.value = value

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_assign_expr(self)


class Binary(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_binary_expr(self)


class Call(Expr):
    def __init__(self, callee: Expr, paren: Token, arguments: List[Expr]):
        self.callee = callee
        self.paren = paren
        self.arguments = arguments

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_call_expr(self)


class Get(Expr):
    def __init__(self, obj: Expr, name: Token):
        self.obj = obj
        self.name = name

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_get_expr(self)


class Grouping(Expr):
    def __init__(self, expression: Expr):
        self.expression = expression

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_grouping_expr(self)


class Literal(Expr):
    def __init__(self, value: Union[str, float, bool]):
        self.value = value

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_literal_expr(self)


class Logical(Expr):
    def __init__(self, left: Expr, operator: Token, right: Expr):
        self.left = left
        self.operator = operator
        self.right = right

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_logical_expr(self)


class Set(Expr):
    def __init__(self, obj, name: Token, value: Expr):
        self.obj = obj
        self.name = name
        self.value = value

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_set_expr(self)


class Super(Expr):
    def __init__(self, keyword: Token, method: Token):
        self.keyword = keyword
        self.method = method

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_super_expr(self)


class This(Expr):
    def __init__(self, keyword: Token):
        self.keyword = keyword

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_this_expr(self)


class Unary(Expr):
    def __init__(self, operator: Token, right: Expr):
        self.operator = operator
        self.right = right

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_unary_expr(self)


class Letiable(Expr):
    def __init__(self, name: Token):
        self.name = name

    def accept(self, visitor: ExprVisitor):
        return visitor.visit_variable_expr(self)
