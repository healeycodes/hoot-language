import time
import asyncio
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from error import RuntimeError
from hoot import Hoot
from tokens import Token
from callable import HootCallable, HootClass, HootInstance


def is_numberable(value):
    try:
        float(value)
    except ValueError:
        return False
    return True


class Input(HootCallable):
    def arity(self, interpreter, arguments):
        return 1

    def call(self, interpreter, arguments, error_token: Token):
        return input(arguments[0])

    def __repr__(self):
        return "<native fn>"


class Read(HootCallable):
    def arity(self, interpreter, arguments):
        return 2

    def call(self, interpreter, arguments, error_token: Token):
        def blocking_read():
            with open(arguments[0], "r") as f:
                return f.read()

        async def main():
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as pool:
                data = await loop.run_in_executor(
                    pool, blocking_read)
                arguments[1].call(interpreter, [data], error_token)
        asyncio.create_task(main())

    def __repr__(self):
        return "<native fn>"


class Write(HootCallable):
    def arity(self, interpreter, arguments):
        return 4

    def call(self, interpreter, arguments, error_token: Token):
        def blocking_write():
            with open(arguments[0], arguments[1]) as f:
                f.write(arguments[2])

        async def main():
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor() as pool:
                data = await loop.run_in_executor(
                    pool, blocking_write)
                if arguments[3]:
                    arguments[3].call(interpreter, [data], error_token)
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
            arguments[0].call(interpreter, [], error_token)
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
                    error_token, f"Error requesting '{url}''. Caught error: {err}")
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
            instance.fields = {
                "body": data["body"].decode("utf-8", errors="ignore"),
                "headers": data["headers"],
            }
            callback.call(interpreter, [instance], error_token)

        asyncio.create_task(read_page())

    def __repr__(self):
        return "<native fn>"


class Import(HootCallable):
    def arity(self, interpreter, arguments):
        return 1

    def call(self, interpreter, arguments, error_token: Token):
        file_name = arguments[0]

        def load():
            hoot = Hoot()
            exit_code = hoot.run_file(file_name)
            if exit_code != 0:
                raise RuntimeError(
                    error_token, f"^^^ above error happened during 'import(\"{file_name}\")'.")
            return hoot.interpreter.environment.values.get("exports")

        with ThreadPoolExecutor() as executor:
            future = executor.submit(load)
            return future.result()

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
                                    name, f"'alter' only accepts numbers. Got '{arg}'.")
                            index = int(arg)
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
                                    name, f"'alter' only accepts numbers. Got '{arg}'.")
                            index = int(arg)
                            to = arguments[1]
                            elements[index] = to
                    return Alter()
                else:
                    raise RuntimeError(
                        name, f"Can't call '{name.lexeme}' on a list.")

            def __repr__(self):
                return str(self.elements)
        return ListInstance(arguments)

    def __repr__(self):
        return "<native fn>"


class MapDataType(HootCallable):
    def arity(self, interpreter, arguments):
        return 0

    def call(self, interpreter, arguments, error_token: Token):
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
        return MapInstance()

    def __repr__(self):
        return "<native fn>"
