# Languages and Compilers Design — Project Stage 1

## Language syntax

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
Comments, parentheses and unary minus are not supported.

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
The additional semantic checker checks literal ranges and assignment
compatibility, but arithmetic-result overflow detection is not implemented.
That detection belongs to the later semantic/code-generation stage.

## Implementation and AST output

The lexer is a hand-written state machine over source bytes.
The parser uses recursive descent and builds a positioned class-based AST.
grammar.ebnf describes the accepted syntax.

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
