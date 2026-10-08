import re
import sys
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

ENCODING = "utf-8-sig"
FRONT_MATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
GUTENBERG_START = re.compile(r"^\*\*\* START OF .*$", re.MULTILINE)
GUTENBERG_END = re.compile(r"^\*\*\* END OF .*$", re.MULTILINE)
BRACKETED = re.compile(r"\[.*\]")
NOT_NARRATION = ("bullet_list_open", "ordered_list_open", "blockquote_open", "table_open")
SKIPPED_INLINE = ("code_inline", "image", "html_inline")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: prose.py FILE|-  (Markdown or a Project Gutenberg text)", file=sys.stderr)
        return 2
    try:
        if argv[0] == "-":
            source = sys.stdin.buffer.read().decode(ENCODING)
        else:
            source = Path(argv[0]).read_text(encoding=ENCODING)
    except (OSError, UnicodeDecodeError) as failure:
        print(f"{argv[0]}: {failure}", file=sys.stderr)
        return 2
    sys.stdout.write(plain(source))
    return 0


def plain(source: str) -> str:
    source = gutenberg_body(source.replace("\r\n", "\n"))
    source = FRONT_MATTER.sub(lambda front: "\n" * front.group().count("\n"), source, count=1)
    lines: list[str] = []
    for line, paragraph in paragraphs(source):
        while len(lines) < line - 1:
            lines.append("")
        if lines and lines[-1]:
            lines.append("")
        lines.append(paragraph)
    return "\n".join(lines) + "\n"


def gutenberg_body(source: str) -> str:
    start = GUTENBERG_START.search(source)
    end = GUTENBERG_END.search(source)
    if not start or not end:
        return source
    before = source[: start.end()]
    return "\n" * before.count("\n") + source[start.end() : end.start()]


def paragraphs(source: str) -> list[tuple[int, str]]:
    tokens = MarkdownIt("commonmark").enable("table").parse(source)
    found: list[tuple[int, str]] = []
    outside = 0
    for position, token in enumerate(tokens):
        if token.type in NOT_NARRATION:
            outside += 1
        elif token.type.replace("_close", "_open") in NOT_NARRATION:
            outside -= 1
        elif token.type == "paragraph_open" and not outside and token.map:
            text = inline_text(tokens[position + 1])
            if narration(text):
                found.append((token.map[0] + 1, text))
    return found


def inline_text(token: Token) -> str:
    parts: list[str] = []
    for child in token.children or []:
        if child.type == "text":
            parts.append(child.content)
        elif child.type in ("softbreak", "hardbreak"):
            parts.append(" ")
        elif child.type in SKIPPED_INLINE:
            parts.append("")
    return " ".join("".join(parts).split())


def narration(text: str) -> bool:
    letters = [character for character in text if character.isalpha()]
    if not letters or not any(letter.islower() for letter in letters):
        return False
    return BRACKETED.fullmatch(text) is None


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
