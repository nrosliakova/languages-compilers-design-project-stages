# Languages and Compilers Design — Course Project

> Implementation status: this working copy implements the agreed Stage 2 language
> plus the Stage 3 loop feature (`while`, `for` over an integer range, `break`).
> It passes the included regression suite using both LLVM JIT and native
> LLVM object code linked with GCC, while retaining the original Stage 1
> fixtures. Standalone `lli` execution still needs verification on the
> submission machine. The Stage 3 optimizer and the Stage 3 program are not in
> this working copy yet.

## Stage 1 language syntax

| Meaning | Syntax |
| --- | --- |
| Signed 32-bit integer | minint |
| Signed 64-bit integer | bigint |
| Boolean | vibe |
| Mutable declaration | 🔓 |
| Immutable declaration | 🔒 |
| True / false | yea / cap |
| Conditional / alternative | chat / nah |
| Program exit | bye |
| Assignment | = |
| Equality / inequality | == / != |
| Arithmetic | +, -, * |
| Boolean negation | ! |
| Block opening / closing | 👇 / 👆 |
| Statement terminator | ; |

Every declaration requires a mutability marker.
Declarations, assignments and bye statements end with a semicolon.
Spaces, tabs and newlines separate tokens but do not end statements.
Block markers need not occupy separate lines.
A chat statement does not take a semicolon after its closing block.
Comments, grouping parentheses and unary minus are not supported.
Stage 2 adds parentheses only for function signatures and calls.

Identifiers use ASCII letters, underscores and digits, and cannot start
with a digit or equal a reserved keyword.
Source files use UTF-8. Columns count bytes, not displayed characters.
The four supported emoji tokens each occupy four UTF-8 bytes.
Use the exact symbols shown above, without added variation selectors.

## Examples

### Types, literals, mutability and assignment

```text
minint 🔓 score{10};
bigint 🔒 large{3000000000};
vibe 🔒 ready{yea};
vibe 🔒 stopped{cap};
score = score + 1;
bye score;
```

### Arithmetic, comparisons and negation

Multiplication has higher precedence than addition and subtraction.
Addition and subtraction group from left to right.
Comparisons have lower precedence than arithmetic.

```text
minint 🔒 value{2 + 3 * 4};
vibe 🔒 same{value == 14};
vibe 🔒 different{value != 0};
vibe 🔒 opposite{!same};
bye different;
```

### Conditions and blocks

A chat statement has an optional nah branch.
Each block must contain at least one statement.
Blocks can contain nested chat statements.

```text
minint 🔓 result{0};
chat yea
👇
    result = 1;
👆
nah
👇
    result = 2;
👆
bye result;
```

## Exit rules

Every program must end with a top-level bye statement.
A block may also end with bye.
No statement can follow bye within the same block or program.

bye accepts a factor: a literal, variable, or ! applied to a factor.
Store an arithmetic expression in a variable before exiting with it.

## Integer ranges and overflow policy

- minint: -2147483648 through 2147483647.
- bigint: -9223372036854775808 through 9223372036854775807.

Arithmetic has type bigint if either operand is bigint;
otherwise it has type minint.
Language rule: an out-of-range arithmetic result must cause an
overflow error rather than silently wrap.

AST mode checks syntax only.
The semantic checker checks literal ranges and assignment compatibility.
Stage 2 code generation checks signed arithmetic results at runtime; overflow
prints the error described below and terminates without wrapping.

## Implementation and AST output

The lexer is a hand-written state machine over source bytes.
The parser uses recursive descent and builds a positioned class-based AST.
The original Stage 1 syntax is described above. `grammar.ebnf` now describes
the implemented extended syntax.

Internal AST types remain i32, i64 and bool.
AST boolean dumps remain true and false.
These canonical names are not source-language keywords.

An error is reported on stderr as:
compilation error: line L:C: message
with a nonzero exit code and no stdout.

## Setup and commands

Requirements: Python 3, Bash for the test runner, and llvmlite.
The current compiler imports llvmlite even in AST mode.

Install llvmlite in your active Python environment:

```bash
python3 -m pip install llvmlite
```

There is no separate build step. Run from the repository root:

```bash
python3 compiler.py --ast tests/ok/if_nested.txt
bash run_stage1_tests.sh
```

Implementation lives in src/.
Root compiler.py and lexer.py provide compatibility entry points.

## Stage 1 tests

The runner checks 16 valid programs in tests/ok against their .ast files,
and 20 lexical/syntax-error programs in tests/ast_err against .expected files.
It checks exit codes, exact outputs and the appropriate empty output stream.

## Additional functionality

The existing compiler also contains semantic checking and LLVM generation.
Those features are separate from the Stage 1 AST pipeline.

```bash
python3 src/compiler.py tests/ok/if_else_assignment.txt output.ll
lli output.ll
```

Execution requires LLVM lli; promotion experiments additionally require opt.
Run python3 check.py for the additional suite: 16 valid execution tests
and 20 semantic/syntax-error tests, all migrated to the new syntax.

Historical fixtures in tests/manual and the loose .src/.out/.err files
directly inside tests retain the old practice syntax. They are not used
by either active test runner.

## Stage 2 language rules

### Compatibility

Keep the Stage 1 types, literals, operators, explicit mutability markers,
semicolon terminators, emoji block markers, whitespace handling and precedence.
New blocks do not require markers on separate lines. New declarations do not
change the existing rules for top-level variables or conditional blocks.
Existing AST names (`i32`, `i64`, `bool`) remain internal implementation names.
The existing `bye` output stays unchanged, including its `true`/`false` spelling.
`say` has its own output rules below.

A `bye` still accepts a factor rather than an unrestricted arithmetic expression.
A function call or field access is a new kind of factor. Store a compound
arithmetic result in a variable before returning it.

### Program and declaration order

A program contains structure declarations first, then global function
declarations, then executable statements, then one final top-level `bye`.
Structures and named functions cannot be declared inside executable blocks.
Inside a structure, fields precede member functions.
Declare a structure before using it as a field type. Variables must be declared
before use. Functions may call themselves and functions declared later;
member functions may call other member functions declared later.

### Functions, parameters and returns

A function has typed parameters, a declared result type and a nonempty body.
Every function and member function ends with a direct `bye value;` in its body;
this intentionally does not require control-flow analysis to prove all paths return.
A `bye` inside a nested conditional also returns from the current function.
Inside a function, `bye` returns a value without printing the top-level exit message.
At top level, `bye` preserves the existing Stage 1 behavior.

```text
fn add(minint a, minint b) -> minint
👇
    minint 🔒 result{a + b};
    bye result;
👆
minint 🔒 answer{add(10, 20)};
bye answer;
```

All arguments are passed as values, including independent copies of structures.
All parameters are immutable. To modify an incoming value, create a mutable local
copy. Modifying such a copy cannot change the caller's object.
A call checks the exact argument count before code generation.
Arguments are evaluated left to right before the call.
Arguments and return values must match the declared type, except that `minint`
may widen to `bigint`. Reject narrowing, boolean/integer conversion and conversion
between distinct structure types.
Calls are expressions and may be arguments to other calls.
A call may also be a standalone statement: execute it and discard the result.
There is no `void` type; an action-only function can return `0` as `minint`.

### Scope and name lookup

Ordinary functions see their parameters and local variables, not top-level
variables. Member functions additionally see the current object's fields.
Variable lookup searches the nearest local scope, then outer local scopes,
then parameters, then object fields for a member function. Top-level variables
are never searched from a function body.
Variables may shadow outer declarations, but duplicate declarations in one
scope are rejected as in Stage 1.

For an unqualified function call inside a member function, search the current
structure's member functions first, then global functions. Global function
calls are allowed from both ordinary and member functions.
A structure cannot give a field and a member function the same name.

### Structures, initialization and field chains

A structure is a named type. Every field has a type and an explicit `🔓` or `🔒`.
Create an object by supplying exactly one value per field, in declaration order.
Missing or extra values are compilation errors; there are no default values.
Nested initializer braces provide values for nested structures.

```text
struct Point
👇
    minint 🔓 x;
    minint 🔒 y;
👆
Point 🔓 p{10, 20};
p.x = 30;
minint 🔒 result{p.y};
bye result;
```

Access fields by name using `.`. Chains such as `circle.center.x` are allowed.
An assignment through a chain requires a mutable root object and mutable fields
at every step, including the final assigned field. Unknown fields are errors.

### Member functions and mutation

Member functions use the ordinary `fn` syntax inside a structure. Fields and
other member functions are available by name according to the lookup rules.
Calling a method passes the original receiver's address, not a copy.
The compiler marks a method as mutating if it assigns an object field directly
or calls another mutating method on the current object, including through
nested receiver fields. Mutation information must propagate through call cycles.
Changing only a local variable does not make a method mutating.

A mutating method requires a mutable receiver: the root object and every field
along its receiver chain must be mutable. Immutable fields cannot be assigned
inside a method. Pure methods may be called on immutable objects.

```text
struct Point
👇
    minint 🔓 x;
    minint 🔓 y;
    fn move(minint dx, minint dy) -> minint
    👇
        x = x + dx;
        y = y + dy;
        bye 0;
    👆
👆
Point 🔓 p{10, 20};
p.move(3, 4);
bye p.x;
```

### Input: listen()

`listen()` takes no arguments and returns `minint`.
Consume one whitespace-separated signed decimal integer token, with an optional
`+` or `-` sign. Its value must be between -2147483648 and 2147483647 inclusive.
Two calls may read tokens from the same line or different lines.
Missing input, malformed input or an out-of-range value prints exactly
`runtime error: invalid input` followed by a newline to stderr and terminates
with a nonzero exit code. Do not silently return zero or truncate the value.
Do not print a normal `bye` result after a runtime error.

```text
minint 🔒 first{listen()};
minint 🔒 second{listen()};
minint 🔒 sum{first + second};
say(sum);
bye sum;
```

The signed input rule does not introduce signed literals or unary minus into
source syntax. For example, `listen()` can read `-3`, while the Stage 1 source
expression rules remain unchanged.

### Output: say(value)

`say` accepts exactly one integer, boolean, string literal or structure value.
Print one trailing newline after the complete value, including a nested object.
A literal is permitted directly as the argument to `say`; there is no string
variable type. Percent signs in literal text are data, not printf directives.

- Integers: signed decimal text.
- Booleans: `yea` or `cap`.
- String literals: their text, without surrounding quotation marks.
- Structures: type name followed by named fields in declaration order, with
  `=` between a field name and value and `, ` between fields. Recurse for nested
  fields. Do not print member functions.

```text
say(yea);
say("hello");
bye 0;
```

The first two output lines are `yea` and `hello`.
An example object line is `Point{x=10, y=20}`.
A nested example is `Circle{center=Point{x=10, y=20}, radius=5}`.

### Checked arithmetic and runtime failure

For every integer `+`, `-` and `*`, the result type is `bigint` if either operand
is `bigint`, otherwise `minint`. Compute with checked signed arithmetic at that
width. If the result is outside that type's range, print exactly
`runtime error: integer overflow` followed by a newline to stderr and terminate
with a nonzero exit code. Do not wrap, continue execution or print the normal
`bye` result after the failure. Output already produced is not retracted.
Out-of-range source literals remain compilation errors.

### Contextual keywords and Stage 1 identifiers

Recognize `fn`, `struct`, `listen` and `say` by syntactic context rather than
reserving them unconditionally. They remain legal identifiers where a variable,
parameter or field name is expected. An existing variable reference such as
`bye say;` retains its Stage 1 meaning; `say(value);` is the new output command.
Likewise, `listen()` is the input built-in, while a bare `listen` can refer to a
variable. Recognize function and structure declaration headers as the new
constructs without rejecting old declarations that use these words as names.
The lexer and parser retain these previously valid Stage 1 identifier uses.
Global functions cannot redefine the built-ins `listen` and `say`; a member
function may use either name because its receiver disambiguates the call.
The internal type names `i32`, `i64` and `bool` are not source type aliases and
cannot be used as structure type names. They remain legal variable names.

### Literal strings and chains after calls

Strings contain literal text, with no escape sequences. Backslashes print as
backslashes: `\n` prints two characters, not a newline. A string cannot contain
an embedded double quote or a physical line break. Percent signs are plain text.

If a function or method returns a structure, a chain may continue with field
access or another member call, for example `makePoint().x`.
A returned structure is a temporary copy. Field reads are allowed, and a method
called on that temporary affects only the copy, not the original source object.
A call result or any path containing a call result cannot be an assignment
target: `makePoint().x = 5;` is rejected. Store the result in a named variable if
it must subsequently be assigned through.

## Stage 3 language rules: loops

Stage 3 adds one feature of my own: loops. `while` repeats a block while a
condition holds, `for` walks an inclusive integer range, and `break` leaves the
innermost loop. Every program that was valid in Stage 2 is still valid and
prints the same.

| Meaning | Syntax |
| --- | --- |
| Repeat while a condition holds | `while` condition block |
| Walk an inclusive integer range | `for` `minint`/`bigint` 🔒 name `from` first `to` last block |
| Leave the innermost loop | `break;` |

A loop takes a block and no trailing semicolon, like `chat`. The condition of a
`while` must be `vibe`. The source language still has no relational operators,
so a condition is built from `==`, `!=` and `!`.

### Example 1: counting down with `while`

```text
minint 🔓 count{0};
minint 🔒 stop{4};
while count != stop
👇
    say(count);
    count = count + 1;
👆
minint 🔓 down{3};
while down != 0
👇
    say(down);
    down = down - 1;
👆
bye count;
```

Prints `0`, `1`, `2`, `3`, then `3`, `2`, `1`, then `Program exit with result 4`.

### Example 2: an inclusive range with a declaration in the body

```text
minint 🔓 total{0};
for minint 🔒 i from 1 to 4
👇
    minint 🔒 square{i * i};
    total = total + square;
👆
say(total);
for minint 🔒 i from 3 to 1
👇
    say(i);
👆
bye total;
```

Prints `30`, then `Program exit with result 30`. The body declares `square` on
every iteration, and the second loop runs zero times because its first value is
above its last.

### Rules

- The range is inclusive at both ends.
- Both bounds are evaluated once, before the first iteration, in the type of the
  counter. A `minint` bound may widen to a `bigint` counter; nothing narrows.
- A first value above the last value runs the body zero times. That is not an error.
- The counter is declared in the header with a locked padlock and cannot be
  reassigned. A body that needs a changing value writes to its own variable.
- The counter is scoped to the loop body. After the loop the name is gone, and a
  counter may shadow an outer variable of the same name without changing it.
- `break` leaves the innermost loop, so a `break` inside a `chat` inside a loop
  leaves the loop. It must be the last statement of its block, exactly as `bye`
  must be, and outside a loop it is an error.
- `while`, `for` and `break` are not reserved words, because Stage 2 programs may
  already use them as names. `minint 🔒 while{5}; bye while;` still compiles:
  `while` starts a loop only when the next token is not `=`, `.`, `(` or `;`;
  `for` starts a loop only when a type name follows it; `break` is a statement
  only as the whole statement `break;`.

### Lowering

`while` becomes three basic blocks: `while.condition`, `while.body` and
`while.end`. The body branches back to the condition, and that branch is the
loop's back edge.

`for` becomes five: `for.condition`, `for.body`, `for.step`, `for.increment` and
`for.end`. The condition compares the counter with the stored last value and
branches into the body while it holds; the body falls through to the step; the
step leaves for `for.end` when the counter has reached the last value, and
otherwise the increment adds one and branches back to `for.condition`.
Leaving before the increment is what keeps the step safe at the top of a type: a
`bigint` loop ending at 9223372036854775807 never adds one to
9223372036854775807, so the single addition the loop performs needs no overflow
check, unlike a `+` written in the source language. `break` branches straight to
the `for.end` or `while.end` block of the innermost loop.

### The IR of `for minint 🔒 i from 1 to 3 👇 say(i); 👆`

Twenty lines of `output.ll` from that program. The increment block is printed
last because the builder appends it after the exit path:

```llvm
for.condition:
  %"for.counter" = load i32, i32* %"i"
  %"for.limit" = load i32, i32* %"i.limit"
  %"for.keep" = icmp sle i32 %"for.counter", %"for.limit"
  br i1 %"for.keep", label %"for.body", label %"for.end"
for.body:
  %"i.value" = load i32, i32* %"i"
  %".6" = call i32 (i8*, ...) @"printf"(i8* bitcast ([3 x i8]* @"print_i32_format" to i8*), i32 %"i.value")
  %".7" = call i32 (i8*, ...) @"printf"(i8* bitcast ([3 x i8]* @"text_format" to i8*), i8* bitcast ([2 x i8]* @"newline" to i8*))
  br label %"for.step"
for.step:
  %"for.counter.1" = load i32, i32* %"i"
  %"for.limit.1" = load i32, i32* %"i.limit"
  %"for.last" = icmp eq i32 %"for.counter.1", %"for.limit.1"
  br i1 %"for.last", label %"for.end", label %"for.increment"
for.increment:
  %"for.counter.2" = load i32, i32* %"i"
  %"for.next" = add i32 %"for.counter.2", 1
  store i32 %"for.next", i32* %"i"
  br label %"for.condition"
```

`for.condition` loads the counter and the last value that `entry` stored before
the loop began and keeps looping while the counter is not greater, so a first
value above the last one falls straight to `for.end`. `for.body` is the user's
block: the two `printf` calls are the one `say(i)` statement, and its final `br`
is the fall-through into the step. The last five lines are the back edge:
`for.step` jumps out when the counter has reached the last value, and only the
`for.increment` block adds one and branches back to `for.condition`.

### The feature's tests

`tests/stage3` holds them, and `run_stage2_tests.py` runs them with everything else.

| File | What it pins |
| --- | --- |
| `ok/loops_while_basic.txt` | two `while` loops, one counting up with `+`, one down with `-` |
| `ok/loops_while_nested.txt` | a `while` inside a `for`, and a body declaring its own variable |
| `ok/loops_for_range.txt` | a `for` with a declaration in the body, an empty range, and a `bigint` range ending at 9223372036854775807 |
| `ok/loops_break.txt` | `break` out of a `while` from inside a `chat`, and out of a `for` |
| `err/loops_while_condition.txt` | a `while` condition that is not `vibe` |
| `err/loops_break_outside.txt` | `break` outside any loop |
| `err/loops_for_counter_mutable.txt` | a counter declared with the open padlock |
| `err/loops_for_counter_type.txt` | a `vibe` counter |
| `err/loops_break_not_last.txt` | a statement after `break` in the same block |

```bash
python3 compiler.py --ast tests/stage3/ok/loops_while_nested.txt
python3 compiler.py tests/stage3/ok/loops_for_range.txt output.ll
python3 run_stage2_tests.py --engine jit
```

## Submission checklist and implementation verification

- Preserve the original Stage 1 fixtures and rerun their AST/output comparisons.
- Implement the draft grammar in the hand-written lexer and recursive-descent parser.
- Port function, structure, member-function, type and mutation checks from practices.
- Add standalone call-statement handling (the practice parser needs extension).
- Adapt practice LLVM generation to the agreed source syntax and output rules.
- Fix the practice single-field nested-structure initializer crash.
- Implement checked integer arithmetic and robust token-validated input.
- Print one positioned compilation error, return nonzero and leave no IR file
  on lexical, syntax or semantic failure; never leak a Python traceback.
- Generate IR only through the builder and write the printed module.
- Provide at least 20 valid and 20 invalid programs, with at least 10 exact-output
  end-to-end cases and at least one `.in` fixture. Cover new rules from both sides.
- Runtime-error tests compare stderr and check a nonzero exit code.
- Prepare `ai_usage_2.txt` with the tools/prompts, reused and changed work,
  reasons for changes and an explanation in Nina's own words.
- Verify Stage 1 is graded and merged, then create `stage2` from updated `main`.
- Include source, grammar, README, disclosure and tests; exclude generated IR,
  binaries, virtual environments and scratch files.
- Open the Stage 2 PR, request the required reviewer, and submit its link and
  `ai_usage_2.txt` in Moodle. Do not merge before review.


## Running the complete regression suite

Run from the repository root using the Python environment with llvmlite installed:

```bash
python3 -m pip install -r requirements.txt
python3 run_stage2_tests.py
```

The default runner uses `lli`. On Linux, if standalone `lli` is unavailable,
local QA can instead verify and execute IR with llvmlite's native LLVM JIT:

```bash
python3 run_stage2_tests.py --engine jit
```

With a C linker driver (`cc`) installed, also test native executables:

```bash
python3 run_stage2_tests.py --engine native
```

This mode verifies the module, emits an object through LLVM, links it with the
C library using `cc`, and runs the executable. Object files and binaries live
in temporary directories, not in the repository.

The JIT helper runs each program in a separate process. It is a QA alternative,
not evidence that the standalone LLVM commands have been tested.
Runtime errors use POSIX `write` for stderr and C `exit` for termination; input
uses `scanf("%c", ...)` to validate a complete decimal token safely.
`printf` handles normal output; generated modules still declare `scanf` and
`printf` as external C-library functions.

The suite checks exact stdout/stderr bytes, exit codes and failed-compilation
output-file cleanup. It includes input fixtures and runtime-error fixtures.
The original `check.py`, `run_tests.sh` and `run_stage1_tests.sh` remain available
for the original Stage 1 suites; use `run_stage2_tests.py` for both stages.

Latest local QA: **236 checks passed, 0 failed in each execution mode**
(LLVM JIT and native object code linked with GCC):

- 59 AST snapshots (16 original Stage 1, 39 Stage 2, 4 Stage 3 loops).
- 59 valid end-to-end execution cases.
- 20 original lexical/syntax-error AST cases.
- 80 invalid compilation cases (20 original, 55 Stage 2, 5 Stage 3 loops).
- 18 runtime-error cases (overflow and invalid input).

Tested with Python 3.13, llvmlite 0.49.0 and LLVM 22.1.0 on Linux, using
both the JIT helper and LLVM-native/GCC linking.
An additional 350 malformed-source mutations produced no unexpected crashes;
accepted mutations had their generated IR verified. This is a smoke check, not
proof that every possible compiler input is handled.

## AI disclosure

`ai_usage.txt` is the Stage 1 record and `ai_usage_2.txt` is the Stage 2 record.
The Stage 3 record, `ai_usage_3.txt`, is not in this working copy yet. It must
name the tools, quote the prompts, say for each part what was taken as it was
and what changed and why, and explain in Nina's own words the code she did not
write, before the Stage 3 submission.
