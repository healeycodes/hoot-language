import os
from expr import ExprVisitor
import time
import asyncio
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from error import RuntimeError
from tokens import Token
from callable import HootCallable, HootClass, HootInstance


def is_numberable(value):
    try:
        float(value)
    except ValueError:
        return False
    return True


class StringInstance(HootInstance):
    def __init__(self, elements: str, error_token: Token):
        super().__init__(HootClass("String", None, {}))
        self.error_token = error_token
        self.elements = list(str(elements))

    def get(self, name: Token):
        elements = self.elements
        if name.lexeme == "at":
            class At(HootCallable):
                def arity(self, interpreter, arguments):
                    return 1

                def call(self, interpreter, arguments, error_token: Token):
                    arg = arguments[0]
                    if not is_numberable(arg):
                        raise RuntimeError(
                            error_token, f"'at' only accepts a number index. Got '{arg}'.")
                    index = int(arg)
                    if arg > len(elements) - 1:
                        raise RuntimeError(
                            error_token, f"'at' out of bounds error.")
                    return elements[index]
            return At()
        elif name.lexeme == "alter":
            class Alter(HootCallable):
                def arity(self, interpreter, arguments):
                    return 2

                def call(self, interpreter, arguments, error_token: Token):
                    arg = arguments[0]
                    to = arguments[1]
                    if not is_numberable(arg):
                        raise RuntimeError(
                            error_token, f"'alter' only accepts a number index. Got '{arg}'.")
                    index = int(arg)
                    if arg > len(elements) - 1:
                        raise RuntimeError(
                            error_token, f"'at' out of bounds error.")
                    elements[index] = str(to)
            return Alter()
        elif name.lexeme == "length":
            class Length(HootCallable):
                def arity(self, interpreter, arguments):
                    return 0

                def call(self, interpreter, arguments, error_token: Token):
                    return len(elements)
            return Length()
        else:
            raise RuntimeError(
                self.error_token, f"Can't call '{name.lexeme}' on a string.")

    def __repr__(self):
        return ''.join(self.elements)


class MapInstance(HootInstance):
    def __init__(self):
        super().__init__(HootClass("Map", None, {}))
        self.store = {}

    def get(self, name: Token):
        store = self.store
        if name.lexeme == "get":
            class Get(HootCallable):
                def arity(self, interpreter, arguments):
                    return 1

                def call(self, interpreter, arguments, error_token: Token):
                    arg = arguments[0]
                    return store.get(arg, None)
            return Get()
        elif name.lexeme == "set":
            class Set(HootCallable):
                def arity(self, interpreter, arguments):
                    return 2

                def call(self, interpreter, arguments, error_token: Token):
                    arg = arguments[0]
                    to = arguments[1]
                    store[arg] = to
            return Set()
        else:
            raise RuntimeError(
                name, f"Can't call '{name.lexeme}' on a map.")

    def items(self):
        return self.store.items()

    def __repr__(self):
        return str(self.store)


class Input(HootCallable):
    def arity(self, interpreter, arguments):
        return 1

    def call(self, interpreter, arguments, error_token: Token):
        return StringInstance(input(arguments[0]), error_token)

    def __repr__(self):
        return "<native fn>"


class Read(HootCallable):
    def arity(self, interpreter, arguments):
        return 2

    def call(self, interpreter, arguments, error_token: Token):
        def blocking_read():
            try:
                with open(arguments[0], "r") as f:
                    return f.read()
            except Exception as err:
                interpreter.hoot.error(
                    error_token, f"Error reading '{arguments[0]}'. Caught error: {err}")
                return None

        async def main():
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as pool:
                data = await loop.run_in_executor(
                    pool, blocking_read)
                arguments[1].call(
                    interpreter, [StringInstance(data, error_token)], error_token)
        asyncio.create_task(main())

    def __repr__(self):
        return "<native fn>"


class Write(HootCallable):
    def arity(self, interpreter, arguments):
        return 4

    def call(self, interpreter, arguments, error_token: Token):
        def blocking_write():
            try:
                with open(arguments[0], arguments[1]) as f:
                    f.write(arguments[2])
                    # wait for file write
                    # https://stackoverflow.com/a/3857543
                    os.fsync(f.fileno())
            except Exception as err:
                interpreter.hoot.error(
                    error_token, f"Error writing '{arguments[0]}'. Caught error: {err}")
                return None

        async def main():
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as pool:
                await loop.run_in_executor(
                    pool, blocking_write)
                if arguments[3]:
                    arguments[3].call(interpreter, [], error_token)
        asyncio.create_task(main())

        with open(arguments[0], arguments[1]) as f:
            f.write(arguments[2])

    def __repr__(self):
        return "<native fn>"


class Clock(HootCallable):
    def arity(self, interpreter, arguments):
        return 0

    def call(self, interpreter, arguments, error_token: Token):
        return time.time()

    def __repr__(self):
        return "<native fn>"


class Delay(HootCallable):
    def arity(self, interpreter, arguments):
        return 2

    def call(self, interpreter, arguments, error_token: Token):
        async def sleeper():
            await asyncio.sleep(arguments[1] / 1000)
            try:
                arguments[0].call(interpreter, [], error_token)
            except Exception as err:
                interpreter.hoot.error(
                    error_token, f"Error in delay callback '{arguments[0]}'. Caught error: {err}")
                return False
        asyncio.create_task(sleeper())
        return 0

    def __repr__(self):
        return "<native fn>"


class Request(HootCallable):
    def arity(self, interpreter, arguments):
        return 5

    def call(self, interpreter, arguments, error_token: Token):
        url, data, headers, method, callback = arguments
        if headers == None:
            headers = {}

        def return_response():
            try:
                request = urllib.request.Request(
                    url, data, headers, method=method)
                response = urllib.request.urlopen(request)
            except Exception as err:
                interpreter.hoot.error(
                    error_token, f"Error requesting '{url}'. Caught error: {err}")
                return False

            return {
                "headers": dict(response.info()),
                "body": response.read(),
            }

        @asyncio.coroutine
        def read_page():
            loop = asyncio.get_event_loop()
            data = yield from loop.run_in_executor(None, lambda: return_response())

            if data == False:
                return

            instance = HootInstance(HootClass("Response", None, {}))

            headers = MapInstance()
            for k, v in data["headers"].items():
                headers.store[k] = v

            instance.fields = {
                "body": StringInstance(data["body"].decode("utf-8", errors="ignore"), error_token),
                "headers": headers,
            }
            callback.call(interpreter, [instance], error_token)

        asyncio.create_task(read_page())

    def __repr__(self):
        return "<native fn>"


class StringDataType(HootCallable):
    def arity(self, interpreter, arguments):
        return 1

    def call(self, interpreter, arguments, error_token: Token):
        return StringInstance(arguments[0], error_token)

    def __repr__(self):
        return "<native fn>"


class ListDataType(HootCallable):
    def arity(self, interpreter, arguments):
        return -1

    def call(self, interpreter, arguments, error_token: Token):
        class ListInstance(HootInstance):
            def __init__(self, elements: list):
                super().__init__(HootClass("List", None, {}))
                self.elements = elements

            def get(self, name: Token):
                elements = self.elements
                if name.lexeme == "at":
                    class At(HootCallable):
                        def arity(self, interpreter, arguments):
                            return 1

                        def call(self, interpreter, arguments, error_token: Token):
                            arg = arguments[0]
                            if not is_numberable(arg):
                                raise RuntimeError(
                                    error_token, f"'at' only accepts a number index. Got '{arg}'.")
                            index = int(arg)
                            if arg > len(elements) - 1:
                                print(arg, len(elements))
                                raise RuntimeError(
                                    error_token, f"'at' out of bounds error.")
                            return elements[index]
                    return At()
                elif name.lexeme == "alter":
                    class Alter(HootCallable):
                        def arity(self, interpreter, arguments):
                            return 2

                        def call(self, interpreter, arguments, error_token: Token):
                            arg = arguments[0]
                            if not is_numberable(arg):
                                raise RuntimeError(
                                    error_token, f"'alter' only accepts a number index. Got '{arg}'.")
                            index = int(arg)
                            if arg > len(elements) - 1:
                                print(arg, len(elements))
                                raise RuntimeError(
                                    error_token, f"'at' out of bounds error.")
                            to = float(arguments[1])
                            elements[index] = to
                    return Alter()
                elif name.lexeme == "length":
                    class Length(HootCallable):
                        def arity(self, interpreter, arguments):
                            return 0

                        def call(self, interpreter, arguments, error_token: Token):
                            return float(len(elements))
                    return Length()
                elif name.lexeme == "push":
                    class Push(HootCallable):
                        def arity(self, interpreter, arguments):
                            return 1

                        def call(self, interpreter, arguments, error_token: Token):
                            arg = arguments[0]
                            if not is_numberable(arg):
                                raise RuntimeError(
                                    error_token, f"'alter' only accepts numbers. Got '{arg}'.")
                            index = int(arg)
                            elements.append(index)
                    return Push()
                elif name.lexeme == "pop":
                    class Pop(HootCallable):
                        def arity(self, interpreter, arguments):
                            return 0

                        def call(self, interpreter, arguments, error_token: Token):
                            return elements.pop()
                    return Pop()
                else:
                    raise RuntimeError(
                        error_token, f"Can't call '{name.lexeme}' on a list.")

            def __repr__(self):
                return str(self.elements)
        return ListInstance(arguments)

    def __repr__(self):
        return "<native fn>"


class MapDataType(HootCallable):
    def arity(self, interpreter, arguments):
        return 0

    def call(self, interpreter, arguments, error_token: Token):
        return MapInstance()

    def __repr__(self):
        return "<native fn>"
