import sys
from error import RuntimeError
from tokens import TokenType
from scanner import Scanner
from resolver import Resolver
from interpreter import Interpreter


class Hoot:
    def __init__(self):
        self.interpreter = Interpreter(self)
        self.had_error = False
        self.had_runtime_error = False

    def main(self):
        if len(sys.argv) > 2:
            print('Usage: hoot.py [script]')
            sys.exit(64)
        elif len(sys.argv) == 2:
            exit_code = self.run_file(sys.argv[1])
            sys.exit(exit_code)
        else:
            self.run_prompt()
            pass

    def run(self, source):
        from parser_ import Parser
        scanner = Scanner(self, source)
        scanner.scan_tokens()
        parser = Parser(self, scanner.tokens)
        statements = parser.parse()

        # stop for parser errors
        if (self.had_error):
            return

        resolver = Resolver(self)
        resolver.resolve_stmts(statements)

        # stop for resolution errors
        if (self.had_error):
            return

        self.interpreter.interpret(statements)

    def run_file(self, path):
        with open(path) as f:
            self.run(f.read())
            if self.had_error:
                return 65
            if self.had_runtime_error:
                return 70
            return 0

    def run_prompt(self):
        while True:
            line = input('> ')
            if len(line) == 0:
                break
            self.reset()
            self.run(line)

    def reset(self):
        self.had_error = False
        self.had_runtime_error = False

    def report(self, line, where, message):
        print(f'[line {line}] Error{where}: {message}', file=sys.stderr)
        self.had_error = True

    def error(self, token, message: str):
        if token.type_ == TokenType.EOF:
            self.report(token.line, " at end", message)
        else:
            self.report(token.line, f" at '{token.lexeme}'", message)

    def runtime_error(self, error: RuntimeError):
        print(f'[line {error.token.line}] {error.message}')
        self.had_runtime_error = True


if __name__ == '__main__':
    hoot = Hoot()
    hoot.main()
