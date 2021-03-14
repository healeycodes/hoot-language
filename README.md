# hoot-lang

Hoot is a dialect of the [Lox](https://github.com/munificent/craftinginterpreters) Programming language.

It's a tree-walking interpreter written with typed Python (3.8). 

Run the integration tests with `python test_hoot.py`. It should pass `mypy .` with no issues.

# Key differences to Lox

I added an [event loop](https://developer.mozilla.org/en-US/docs/Web/JavaScript/EventLoop). The Hoot standard library has asynchronous functions that can be used with callbacks e.g. web requests, file reading/writing.

Let's print the headers from a HTTP response.

```
fun print_headers(response) {
    print response.get("headers");
}

// request params: url, data, headers, method, callback
request("http://google.com", nil, nil, "GET", print_headers);

print "This message will show before print_headers is called!";
```

<br>

There are also `string()`, `list()`, and `map()` types.

```
// string and list have `at(index)` and `alter(index, element)`
let some_text = string("Hello, World!");
some_text.alter(12, "?");
print some_text; // "Hello, World?"

// list
let some_numbers = list(1, -1, 0.5, 12, 2);
print some_numbers.at(1); // -1

// map uses `get(key)` and `set(key, element)
let food_store = map();
food_store.set("burger)
```

