from enum import Enum, auto
from typing import Dict, List, TYPE_CHECKING
from tokens import Token
from stmt import Break
from expr import Letiable, This
# from hoot import Hoot


class FunctionType(Enum):
    NONE = auto()
    FUNCTION = auto()
    INITIALIZR = auto()
    METHOD = auto()


class ClassType(Enum):
    NONE = auto()
    CLASS = auto()
    SUBCLASS = auto()


class StatementType(Enum):
    NONE = auto()
    WHILE = auto()


class Resolver:
    def __init__(self, hoot):
        self.interpreter = hoot.interpreter
        self.hoot = hoot
        self.scopes: List[Dict[str, bool]] = [{}]
        self.current_function = FunctionType.NONE
        self.current_class = ClassType.NONE
        self.current_statement = StatementType.NONE

    def visit_block_stmt(self, stmt):
        self.begin_scope()
        self.resolve_stmts(stmt.statements)
        self.end_scope()

    def visit_class_stmt(self, stmt):
        enclosing_class = self.current_class
        self.current_class = ClassType.CLASS

        self.declare(stmt.name)
        self.define(stmt.name)

        if stmt.superclass != None and stmt.name.lexeme == stmt.superclass.name.lexeme:
            self.hoot.error(stmt.superclass.name,
                            "A class can't inherit from itself.")

        if stmt.superclass != None:
            self.current_class = ClassType.SUBCLASS
            self.resolve_expr(stmt.superclass)

        if stmt.superclass != None:
            self.begin_scope()
            self.scopes[-1]["super"] = True

        self.begin_scope()
        self.scopes[-1]["this"] = True

        for method in stmt.methods:
            declaration = FunctionType.METHOD
            if method.name.lexeme == "init":
                declaration = FunctionType.INITIALIZR
            self.resolve_function(method, declaration)

        self.end_scope()
        if stmt.superclass != None:
            self.end_scope()

        self.current_class = enclosing_class

    def visit_expression_stmt(self, stmt):
        self.resolve_stmt(stmt.expression)

    def visit_function_stmt(self, stmt):
        self.declare(stmt.name)
        self.define(stmt.name)
        self.resolve_function(stmt, FunctionType.FUNCTION)

    def visit_if_stmt(self, stmt):
        self.resolve_stmt(stmt.condition)
        self.resolve_stmt(stmt.then_branch)
        if stmt.else_branch != None:
            self.resolve_stmt(stmt.else_branch)

    def visit_print_stmt(self, stmt):
        self.resolve_expr(stmt.expression)

    def visit_return_stmt(self, stmt):
        if stmt.value != None:
            if self.current_function == FunctionType.INITIALIZR:
                self.hoot.error(
                    stmt.keyword, "Can't return a value from an initializer.")
            self.resolve_expr(stmt.value)

    def visit_while_stmt(self, stmt):
        self.resolve_expr(stmt.condition)
        enclosing = self.current_statement
        self.current_statement = StatementType.WHILE
        self.resolve_expr(stmt.body)
        self.current_statement = enclosing

    def visit_break_stmt(self, stmt):
        if self.current_statement != StatementType.WHILE:
            self.hoot.error(Token(Break, 'break', None, "?"),
                            "Can't use 'break' outside of a loop.")

    def visit_var_stmt(self, stmt):
        self.declare(stmt.name)
        if stmt.initializer != None:
            self.resolve_expr(stmt.initializer)
        self.define(stmt.name)

    def visit_variable_expr(self, expr):
        if len(self.scopes) == 0:
            if expr.name.lexeme in self.scopes[-1] and self.scopes[-1][expr.name.lexeme] == False:
                self.hoot.error(expr.keyword,
                                "Can't read local variable in its own initializer.")
        self.resolve_local(expr, expr.name)

    def visit_assign_expr(self, expr):
        self.resolve_expr(expr.value)
        self.resolve_local(expr, expr.name)

    def visit_binary_expr(self, expr):
        self.resolve_expr(expr.left)
        self.resolve_expr(expr.right)

    def visit_call_expr(self, expr):
        self.resolve_expr(expr.callee)
        for argument in expr.arguments:
            self.resolve_expr(argument)

    def visit_get_expr(self, expr):
        self.resolve_expr(expr.obj)

    def visit_grouping_expr(self, expr):
        self.resolve_expr(expr.expression)

    def visit_literal_expr(self, expr):
        pass

    def visit_logical_expr(self, expr):
        self.resolve_expr(expr.left)
        self.resolve_expr(expr.right)

    def visit_set_expr(self, expr):
        self.resolve_expr(expr.value)
        self.resolve_expr(expr.obj)

    def visit_super_expr(self, expr):
        if self.current_class == ClassType.NONE:
            self.hoot.error(
                expr.keyword, "Can't use 'super' outside of a class.")
        elif self.current_class != ClassType.SUBCLASS:
            self.hoot.error(
                expr.keyword, "Can't use 'super' in a class with no superclass.")
        self.resolve_local(expr, expr.keyword)

    def visit_this_expr(self, expr: This):
        if self.current_class == ClassType.NONE:
            self.hoot.error(
                expr.keyword, "Can't use 'this' outside of a class.")
        self.resolve_local(expr, expr.keyword)

    def visit_unary_expr(self, expr):
        self.resolve_expr(expr.right)

    def visit_var_expr(self, expr: Letiable):
        if len(self.scopes) != 0:
            if expr.name.lexeme in self.scopes and self.scopes[expr.name.lexeme] == False:
                self.interpreter.hoot.error(
                    expr.name, "Can't read local variable in its own initializer.")
        self.resolve_local(expr, expr.name)

    def resolve_stmts(self, statements):
        for statement in statements:
            self.resolve_stmt(statement)

    def resolve_stmt(self, stmt):
        stmt.accept(self)

    def resolve_expr(self, expr):
        expr.accept(self)

    def resolve_function(self, function, function_type):
        enclosing_function = self.current_function
        self.current_function = function_type

        self.begin_scope()
        for param in function.params:
            self.declare(param)
            self.define(param)
        self.resolve_stmts(function.body)
        self.end_scope()
        self.current_function = enclosing_function

    def begin_scope(self):
        self.scopes.append({})

    def end_scope(self):
        self.scopes.pop()

    def declare(self, name: Token):
        if len(self.scopes) == 0:
            return None
        scope = self.scopes[-1]
        if name.lexeme in scope:
            self.hoot.error(name,
                            "Already variable with this name in this scope.")
        scope[name.lexeme] = False

    def define(self, name: Token):
        if len(self.scopes) == 0:
            return None
        self.scopes[-1][name.lexeme] = True

    def resolve_local(self, expr, name: Token):
        for i in range(len(self.scopes)-1, -1, -1):
            if name.lexeme in self.scopes[i]:
                self.interpreter.resolve(expr, len(self.scopes) - 1 - i)
                return
