from dataclasses import dataclass


KEYWORDS = {
    "minint", "bigint", "vibe",
    "chat", "nah", "bye", "yea", "cap",
}

EMOJI_TOKENS = {
    "\U0001f513".encode("utf-8"): "keyword",
    "\U0001f512".encode("utf-8"): "keyword",
    "\U0001f447".encode("utf-8"): "block",
    "\U0001f446".encode("utf-8"): "block",
}


class LexError(Exception):
    def __init__(self, line, column, message):
        self.line = line
        self.column = column
        self.message = message
        super().__init__(message)


@dataclass
class Token:
    kind: str
    text: str
    line: int
    column: int


def is_letter(byte):
    return (
        ord("A") <= byte <= ord("Z")
        or ord("a") <= byte <= ord("z")
        or byte == ord("_")
    )


def is_digit(byte):
    return ord("0") <= byte <= ord("9")


def display_byte(byte):
    if byte is None:
        return "end of input"
    if 32 <= byte <= 126:
        return chr(byte)
    return f"\\x{byte:02x}"


def lex(data):
    tokens = []
    state = "START"
    i = 0
    line = column = 1
    start = 0
    start_line = start_column = 1
    emoji_bytes = b""

    while True:
        byte = data[i] if i < len(data) else None

        if state == "START":
            if byte is None:
                break

            start = i
            start_line = line
            start_column = column

            if byte in (32, 9, 13, 10):
                pass
            elif is_letter(byte):
                state = "IDENT"
            elif is_digit(byte):
                state = "NUMBER"
            elif byte in (ord("{"), ord("}")):
                tokens.append(Token("block", chr(byte), line, column))
            elif byte == ord(";"):
                tokens.append(Token("separator", ";", line, column))
            elif byte in (ord("+"), ord("-"), ord("*")):
                tokens.append(Token("operator", chr(byte), line, column))
            elif byte == ord("="):
                state = "EQUAL"
            elif byte == ord("!"):
                state = "BANG"
            elif any(sequence[0] == byte for sequence in EMOJI_TOKENS):
                state = "EMOJI"
                emoji_bytes = bytes([byte])
            else:
                raise LexError(
                    line, column,
                    f"unexpected byte '{display_byte(byte)}'",
                )

        elif state == "IDENT":
            if byte is not None and (is_letter(byte) or is_digit(byte)):
                pass
            else:
                text = data[start:i].decode("ascii")
                kind = "keyword" if text in KEYWORDS else "identifier"
                tokens.append(Token(kind, text, start_line, start_column))
                state = "START"
                continue

        elif state == "NUMBER":
            if byte is not None and is_digit(byte):
                pass
            elif byte is not None and is_letter(byte):
                raise LexError(
                    line, column,
                    "a letter cannot appear inside a number",
                )
            else:
                text = data[start:i].decode("ascii")
                tokens.append(Token("number", text, start_line, start_column))
                state = "START"
                continue

        elif state in {"EQUAL", "BANG"}:
            first = "=" if state == "EQUAL" else "!"
            if byte == ord("="):
                tokens.append(
                    Token("operator", first + "=", start_line, start_column)
                )
                state = "START"
            else:
                tokens.append(
                    Token("operator", first, start_line, start_column)
                )
                state = "START"
                continue

        elif state == "EMOJI":
            if byte is None:
                raise LexError(
                    start_line, start_column,
                    "incomplete emoji token",
                )

            emoji_bytes += bytes([byte])

            if emoji_bytes in EMOJI_TOKENS:
                tokens.append(Token(
                    EMOJI_TOKENS[emoji_bytes],
                    emoji_bytes.decode("utf-8"),
                    start_line,
                    start_column,
                ))
                state = "START"
            elif not any(
                sequence.startswith(emoji_bytes)
                for sequence in EMOJI_TOKENS
            ):
                raise LexError(
                    start_line, start_column,
                    "unknown emoji or invalid UTF-8 token",
                )

        if byte == 10:
            line += 1
            column = 1
        else:
            column += 1
        i += 1

    tokens.append(Token("eof", "", line, column))
    return tokens
