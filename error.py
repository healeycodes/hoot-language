from tokens import Token


class ParseError(Exception):
    def __init__(self, message: str):
        self.message = message


class RuntimeError(Exception):
    def __init__(self, token: Token, message: str):
        self.token = token
        self.message = message


class BreakJump(RuntimeError):
    pass
