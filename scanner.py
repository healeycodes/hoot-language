from typing import List
from tokens import Token, TokenType


class Scanner:
    def __init__(self, hoot, source) -> None:
        self.hoot = hoot
        self.source = source
        self.start = 0
        self.current = 0
        self.line = 1
        self.tokens: List[Token] = []
        self.keywords = {
            'and': TokenType.AND,
            'break': TokenType.BREAK,
            'class': TokenType.CLASS,
            'else':   TokenType.ELSE,
            'false':  TokenType.FALSE,
            'for':    TokenType.FOR,
            'fun':    TokenType.FUN,
            'if':     TokenType.IF,
            'nil':    TokenType.NIL,
            'or':     TokenType.OR,
            'print':  TokenType.PRINT,
            'return': TokenType.RETURN,
            'super':  TokenType.SUPER,
            'this':   TokenType.THIS,
            'true':   TokenType.TRUE,
            'let':    TokenType.LET,
            'while':  TokenType.WHILE,
        }

    def scan_tokens(self):
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()

        self.tokens.append(Token(TokenType.EOF, '', None, self.line))

    def scan_token(self):
        c = self.advance()
        if c == '(':
            self.add_token(TokenType.LEFT_PAREN, None)
        elif c == ')':
            self.add_token(TokenType.RIGHT_PAREN, None)
        elif c == '{':
            self.add_token(TokenType.LEFT_BRACE, None)
        elif c == '}':
            self.add_token(TokenType.RIGHT_BRACE, None)
        elif c == ',':
            self.add_token(TokenType.COMMA, None)
        elif c == '.':
            self.add_token(TokenType.DOT, None)
        elif c == '-':
            self.add_token(TokenType.MINUS, None)
        elif c == '+':
            self.add_token(TokenType.PLUS, None)
        elif c == ';':
            self.add_token(TokenType.SEMICOLON, None)
        elif c == '*':
            self.add_token(TokenType.STAR, None)
        elif c == '!':
            self.add_token(
                TokenType.BANG_EQUAL if self.match(
                    '=') else TokenType.BANG, None
            )
        elif c == '=':
            self.add_token(
                TokenType.EQUAL_EQUAL if self.match(
                    '=') else TokenType.EQUAL, None
            )
        elif c == '<':
            self.add_token(
                TokenType.LESS_EQUAL if self.match(
                    '=') else TokenType.LESS, None
            )
        elif c == '>':
            self.add_token(
                TokenType.GREATER_EQUAL if self.match(
                    '=') else TokenType.GREATER, None
            )
        elif c == '/':
            if self.match('/'):
                # a comment goes until the end of the line
                while self.peek() != '\n' and not self.is_at_end():
                    self.advance()
            else:
                self.add_token(TokenType.SLASH, None)
        elif c in [' ', '\r', '\t']:
            return
        elif c == '\n':
            self.line += 1
        elif c == '"':
            self.string()
        else:
            if c.isdigit():
                self.number()
            elif c.isalpha():
                self.identifier()
            else:
                # TODO: check this is correct
                self.hoot.report(self.line, '', 'Unexpected character.')

    def identifier(self):
        while self.is_alpha_numeric(self.peek()):
            self.advance()

        text = self.source[self.start:self.current]
        type_ = self.keywords[text] if text in self.keywords else TokenType.IDENTIFIER
        self.add_token(type_, None)

    def number(self):
        while self.peek().isdigit():
            self.advance()

        # look for fractional part
        if self.peek() == '.' and self.peek_next().isdigit():
            # consume the "."
            self.advance()

        while self.peek().isdigit():
            self.advance()

        self.add_token(TokenType.NUMBER, float(
            self.source[self.start:self.current]))

    def string(self):
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
            self.advance()

        if self.is_at_end():
            self.hoot.error(Token(TokenType.EOF, None, None,
                                  self.line), 'Unterminated string.')
            return

        # the closing '"'
        self.advance()

        # trim the surrounding quotes
        value = self.source[self.start+1: self.current-1]
        self.add_token(TokenType.STRING, value)

    def match(self, expected):
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def peek(self):
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def is_digit(self, c):
        return c.isdigit()

    def is_alpha(self, c):
        return c.isalpha() or c == '_'

    def is_alpha_numeric(self, c):
        return self.is_digit(c) or self.is_alpha(c)

    def peek_next(self):
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current+1]

    def advance(self):
        self.current += 1
        return self.source[self.current-1]

    def add_token(self, type_, literal):
        text = self.source[self.start:self.current]
        self.tokens.append(Token(type_, text, literal, self.line))

    def is_at_end(self):
        return self.current >= len(self.source)
