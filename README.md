# Hoot Lang

A general-purpose interpreted scripting language with an event loop. It's dynamically typed, with classes, inheritance, and closures. It's an implementation and extension of the [Lox](https://github.com/munificent/craftinginterpreters) Programming language.

Hoot extends Lox by introducing an event loop for non-blocking I/O, more complex types (string, list, map), and a tiny standard library (web requests, file reading/writing, delay functions).

Why? I wrote it to learn more about interpreters! It uses Python 3.8 and no additional libraries.

<br>

Run the integration tests with `python test_hoot.py`. It should also pass `mypy .` with no issues.

Run a program with `python hoot.py file.hoot`.

Open the REPL with `python hoot.py`.

<br>

## Example programs

Printing the headers from a HTTP response.

```
fun print_headers(response) {
    print response.headers; // This is a map()
}

request("https://google.com", nil, nil, "GET", print_headers);

print "This message will print before print_headers is called.";
```

<br>

Delaying a function.

```
fun make_logger(time) {
    fun logger () {
        print string(time) + "ms";
    }
    return logger;
}

delay(make_logger(0), 0); // 0ms delay

print "This message prints first because each task 'Runs-to-completion' a la JavaScript";

delay(make_logger(50), 50);
delay(make_logger(100), 100);
```

<br>

Everyone's favorite inefficient sorting algorithm.

```
fun bubble_sort(numbers) {
    for (let i = 0; i < numbers.length() - 1; i = i + 1) {
        for (let j = 0; j < numbers.length() - 1; j = j + 1) {
            if (numbers.at(j) > numbers.at(j + 1)) {
                let tmp = numbers.at(j);
                numbers.alter(j, numbers.at(j + 1));
                numbers.alter(j + 1, tmp);
            }
        }
    }
    return numbers;
}


let unordered_numbers = list(1, -1, 0.5, 12, 2);
print bubble_sort(unordered_numbers);
```

<br>

Read a file, print the length, append to it, then print the new length.

```
fun show_length(text) {
    print "File length: " + string(text.length());
}

fun show_original_length(text) {
    print "File length: " + string(text.length());
    
    fun callback() {
        read("examples/test_file.txt", show_length);
    }
    write("examples/test_file.txt", "a", "More text", callback);
}

read("examples/test_file.txt", show_original_length);
```

<br>

## Language reference

Variables

```
let num = 0; // All numbers are floats
let raw = "raw string";
```

<br>

Types

```
// string has `at(index)`, `alter(index, element)`, `length()`
let some_text = string("Hello, World!");
some_text.alter(12, "?");
print some_text; // "Hello, World?"

// list has `at(index)`, `alter(index, element)`, `length()`, `push(element)`, and `pop()`
let some_numbers = list(1, -1, 0.5, 12, 2);
print some_numbers.at(1); // -1

// map has `get(key)` and `set(key, element)`
let food_store = map();
food_store.set("burgers", 20);
```

<br>

Loops

```
for (let i = 0; i < 5; i = i + 1) {
    print i;
}

while (true) {
    print "Um.. let's quit this infinite loop.;
    break;
}
```

<br>

Functions/closures

```
fun make_adder(y) {
   fun adder(x) {
       return x + y;
   }
   return adder;
}

let my_adder = make_adder(10);
adder(5); // 15
```

<br>

Classes

```
// Lifted this example straight from chapter 13 of Crafting Interpreters
class Doughnut {
  cook() {
    print "Fry until golden brown.";
  }
}

class BostonCream < Doughnut {
  cook() {
    super.cook();
    print "Pipe full of custard and coat with chocolate.";
  }
}

BostonCream().cook();
```

<br>

## Standard library

See `native.py` for implementation details.

<br>

`input(prompt)` — Returns standard input.

`read(file_path, callback)` — reads a UTF-8 compatible file and passes it as the first argument to _callback_.

`write(file_path, mode, data, callback)` — writes _data_ to a file. _mode_ is the same as Python's `open`. Calls _callback_ without passing any arguments.

`clock()` — UNIX seconds.

`delay(milliseconds, callback)` — like setTimeout in JavaScript.

`request(url, data, headers, http_method, callback)` — _callback_ is passed a response instance with the fields `body` and `header` which can be accessed via `.` dot.

<br>

## Licence

MIT.
