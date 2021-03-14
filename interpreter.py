import asyncio
from tokens import Token, TokenType
from typing import Dict, List
from error import BreakJump, RuntimeError
from environment import Environment
from callable import HootClass, HootFunction, HootInstance, ReturnBubble
from expr import Assign, Binary, Call, Expr, ExprVisitor, Grouping, Literal, Logical, Set, Super, This, Unary, Letiable
from stmt import Block, Expression, Let, Print, Return, Stmt, While, Break
from native import Clock, Delay, StringInstance, StringDataType, ListDataType, MapDataType, Request, Input, Write, Read


class Interpreter(ExprVisitor):
    def __init__(self, hoot):
        self.hoot = hoot
        self.globals = Environment(None)
        self.environment = self.globals
        self.locals: Dict[Expr, int] = {}

        self.globals.define('input', Input())
        self.globals.define('read', Read())
        self.globals.define('write', Write())
        self.globals.define('clock', Clock())
        self.globals.define('delay', Delay())
        self.globals.define('request', Request())
        self.globals.define('string', StringDataType())
        self.globals.define('list', ListDataType())
        self.globals.define('map', MapDataType())

    def interpret(self, statements: List[Stmt]):
        async def main():
            try:
                for statement in statements:
                    self.execute(statement)
            except RuntimeError as error:
                self.hoot.runtime_error(error)

        def get_pending_tasks():
            tasks = asyncio.all_tasks()
            pending = [task for task in tasks if task !=
                       run_main_task and not task.done()]
            return pending

        async def run_main():
            await main()

            while True:
                pending_tasks = get_pending_tasks()
                if len(pending_tasks) == 0:
                    return
                await asyncio.gather(*pending_tasks)

        loop = asyncio.new_event_loop()
        run_main_coro = run_main()
        run_main_task = loop.create_task(run_main_coro)
        loop.run_until_complete(run_main_task)
        loop.close()

    def visit_literal_expr(self, expr: Literal):
        return expr.value

    def visit_logical_expr(self, expr: Logical):
        left = self.evaluate(expr.left)
        if expr.operator.type_ == TokenType.OR:
            if self.is_truthy(left):
                return left
        else:
            if not self.is_truthy(left):
                return left
        return self.evaluate(expr.right)

    def visit_set_expr(self, expr: Set):
        obj = self.evaluate(expr.obj)
        if not type(obj) == HootInstance:
            raise RuntimeError(expr.name, "Only instances have fields.")

        value = self.evaluate(expr.value)
        obj.set_(expr.name, value)
        return value

    def visit_super_expr(self, expr: Super):
        distance = self.locals.get(expr) or -1
        if distance == -1:
            raise RuntimeError(
                expr.keyword, f"Distance error. Probably because an earlier resolving problem.")
        superclass = self.environment.get_at(distance, "super")
        obj = self.environment.get_at(distance - 1, "this")
        method = superclass.find_method(expr.method.lexeme)

        if method == None:
            raise RuntimeError(
                expr.method, f"Undefined property '{expr.method.lexeme}'.")

        return method.bind(obj)

    def visit_this_expr(self, expr: This):
        return self.look_up_variable(expr.keyword, expr)

    def visit_grouping_expr(self, expr: Grouping):
        return self.evaluate(expr.expression)

    def evaluate(self, expr: Expr):
        return expr.accept(self)

    def execute(self, stmt: Stmt):
        stmt.accept(self)

    def resolve(self, expr: Expr, depth: int):
        self.locals[expr] = depth

    def visit_block_stmt(self, stmt: Block):
        self.execute_block(stmt.statements, Environment(self.environment))

    def visit_class_stmt(self, stmt):
        superclass = None
        if stmt.superclass != None:
            superclass = self.evaluate(stmt.superclass)
            if type(superclass) != HootClass:
                raise RuntimeError(stmt.superclass.name,
                                   "Superclass must be a class.")
        self.environment.define(stmt.name.lexeme, None)

        if stmt.superclass != None:
            self.environment = Environment(self.environment)
            self.environment.define("super", superclass)

        methods = {}
        for method in stmt.methods:
            function = HootFunction(
                method, self.environment, method.name.lexeme == "init")
            methods[method.name.lexeme] = function

        klass = HootClass(stmt.name.lexeme, superclass, methods)

        if superclass != None:
            self.environment = self.environment.enclosing

        self.environment.assign(stmt.name, klass)

    def execute_block(self, statements, environment):
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self.execute(statement)
        finally:
            self.environment = previous

    def visit_expression_stmt(self, stmt: Expression):
        self.evaluate(stmt.expression)

    def visit_function_stmt(self, stmt):
        function = HootFunction(stmt, self.environment, False)
        self.environment.define(stmt.name.lexeme, function)

    def visit_if_stmt(self, stmt):
        if self.is_truthy(self.evaluate(stmt.condition)):
            self.execute(stmt.then_branch)
        elif stmt.else_branch != None:
            self.execute(stmt.else_branch)

    def visit_print_stmt(self, stmt: Print):
        value = self.evaluate(stmt.expression)
        print(self.stringify(value))

    def visit_return_stmt(self, stmt: Return):
        value = None
        if stmt.value != None:
            value = self.evaluate(stmt.value)
        raise ReturnBubble(value)

    def visit_var_stmt(self, stmt: Let):
        value = None
        if stmt.initializer != None:
            value = self.evaluate(stmt.initializer)

        self.environment.define(stmt.name.lexeme, value)

    def visit_while_stmt(self, stmt: While):
        while self.is_truthy(self.evaluate(stmt.condition)):
            try:
                self.execute(stmt.body)
            except BreakJump:
                break

    def visit_break_stmt(self, stmt: Break):
        raise BreakJump(
            Token(TokenType.BREAK, "break", None, "?"), "Breaking.")

    def visit_assign_expr(self, expr: Assign):
        value = self.evaluate(expr.value)

        distance = self.locals[expr] if expr in self.locals else None
        if distance != None:
            self.environment.assign_at(distance, expr.name, value)
        else:
            self.globals.assign(expr.name, value)

        return value

    def visit_binary_expr(self, expr: Binary):
        left = self.evaluate(expr.left)
        right = self.evaluate(expr.right)

        if expr.operator.type_ == TokenType.MINUS:
            self.check_number_operands(expr.operator, left, right)
            return left - right
        elif expr.operator.type_ == TokenType.SLASH:
            self.check_number_operands(expr.operator, left, right)
            return left / right
        elif expr.operator.type_ == TokenType.STAR:
            self.check_number_operands(expr.operator, left, right)
            return left * right
        elif expr.operator.type_ == TokenType.PLUS:
            if type(left) == str and type(right) == str \
                    or type(left) == float and type(right) == float:
                return left + right
            if type(left) == StringInstance and type(right) == StringInstance:
                return StringInstance(''.join(left.elements) + ''.join(right.elements), expr.operator)
            if type(left) == str and type(right) == StringInstance:
                return StringInstance(left + ''.join(right.elements), expr.operator)
            if type(left) == StringInstance and type(right) == str:
                return StringInstance(''.join(left.elements) + right, expr.operator)
            raise RuntimeError(
                expr.operator, "Operands must be two numbers or two strings.")
        elif expr.operator.type_ == TokenType.GREATER:
            self.check_number_operands(expr.operator, left, right)
            return left > right
        elif expr.operator.type_ == TokenType.GREATER_EQUAL:
            self.check_number_operands(expr.operator, left, right)
            return left >= right
        elif expr.operator.type_ == TokenType.LESS:
            self.check_number_operands(expr.operator, left, right)
            return left < right
        elif expr.operator.type_ == TokenType.LESS_EQUAL:
            self.check_number_operands(expr.operator, left, right)
            return left <= right
        elif expr.operator.type_ == TokenType.BANG_EQUAL:
            return not self.is_equal(left, right)
        elif expr.operator.type_ == TokenType.EQUAL_EQUAL:
            return self.is_equal(left, right)

    def visit_call_expr(self, expr: Call):
        callee = self.evaluate(expr.callee)

        arguments = []
        for argument in expr.arguments:
            arguments.append(self.evaluate(argument))

        if not hasattr(callee, 'call'):
            raise RuntimeError(
                expr.paren, "Can only call functions and classes.")

        function: HootFunction = callee
        arity = function.arity(self, arguments)
        if len(arguments) != arity and arity != -1:
            raise RuntimeError(
                expr.paren, f"Expected {arity} arguments but got {len(arguments)}.")

        return function.call(self, arguments, expr.paren)

    def visit_get_expr(self, expr):
        obj = self.evaluate(expr.obj)
        if isinstance(obj, HootInstance):
            return obj.get(expr.name)

        raise RuntimeError(expr.name, "Only instances have properties")

    def visit_unary_expr(self, expr: Unary):
        right = self.evaluate(expr.right)

        if expr.operator.type_ == TokenType.MINUS:
            self.check_number_operand(expr.operator, right)
            return -right
        elif expr.operator.type_ == TokenType.BANG:
            return not self.is_truthy(right)

    def visit_variable_expr(self, expr: Letiable):
        return self.look_up_variable(expr.name, expr)

    def look_up_variable(self, name: Token, expr: Expr):
        distance = self.locals[expr] if expr in self.locals else None
        if distance != None:
            return self.environment.get_at(distance, name.lexeme)
        else:
            return self.globals.get(name)

    def check_number_operand(self, operator: Token, operand):
        if type(operand) == float:
            return
        raise RuntimeError(operator, "Operand must be a number")

    def check_number_operands(self, operator: Token, left, right):
        if type(left) == float and type(right) == float:
            return
        raise RuntimeError(operator, "Operand must be a number")

    def is_truthy(self, value):
        # Hoot follows Ruby’s simple rule: false and nil are falsey,
        # and everything else is truthy.
        if value == None:
            return False
        if type(value) == bool:
            return value
        return True

    def is_equal(self, left, right):
        return left == right

    def stringify(self, value):
        if value == None:
            return 'nil'
        return str(value)
