"""
Some notes in case I ever want to come back to this.
"""

# class AstPrinter(ExprVisitor):
#     def print(self, expr: Expr):
#         return expr.accept(self)

#     def visit_binary_expr(self, expr: Binary):
#         return self.parenthesize(expr.operator.lexeme, [expr.left, expr.right])

#     def visit_grouping_expr(self, expr: Grouping):
#         return self.parenthesize("group", [expr.expression])

#     def visit_literal_expr(self, expr: Literal):
#         if expr.value == None:
#             return 'nil'
#         return str(expr.value)

#     def visit_unary_expr(self, expr: Unary):
#         return self.parenthesize(expr.operator.lexeme, [expr.right])

#     def parenthesize(self, name, exprs: List[Union[Expr, None]]):
#         return f'({name} {" ".join([expr.accept(self) for expr in exprs if expr])})'
