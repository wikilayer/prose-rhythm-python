import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .measure import (
    ENGLISH,
    LONG_SENTENCES,
    SPREAD,
    SUBJECT_RUNS,
    UNIFORM_PARAGRAPHS,
    Finding,
    Run,
    Tally,
    Verdict,
    judge,
    places,
    tally,
)
from .norms import MIN, Language, UnknownLanguage, Unreadable, language, stripped

CLEAN = 0
FOUND = 1
UNUSABLE = 2
STDIN = "-"
ENCODING = "utf-8-sig"
EXCERPT = 60


class Unopenable(Exception):
    pass


@dataclass(frozen=True)
class Measured:
    name: str
    tally: Tally
    verdict: Verdict
    runs: tuple[Run, ...]
    lines: tuple[int, ...]


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.paths.count(STDIN) > 1:
        print("stdin can be read only once", file=sys.stderr)
        return UNUSABLE
    try:
        rules = language(arguments.language)
    except (Unreadable, UnknownLanguage) as failure:
        print(failure, file=sys.stderr)
        return UNUSABLE

    unusable = False
    found = False
    for name in arguments.paths:
        try:
            one = measure(name, rules)
        except Unopenable as failure:
            print(failure, file=sys.stderr)
            unusable = True
            continue
        print(report(one, arguments.places, rules))
        found = found or bool(one.verdict.findings)
    if unusable:
        return UNUSABLE
    return FOUND if found else CLEAN


def measure(name: str, rules: Language) -> Measured:
    try:
        raw = sys.stdin.buffer.read() if name == STDIN else Path(name).read_bytes()
        text = raw.decode(ENCODING)
    except OSError as failure:
        raise Unopenable(f"{name}: {failure.strerror or failure}") from failure
    except UnicodeDecodeError as failure:
        raise Unopenable(f"{name}: not UTF-8 text ({failure.reason})") from failure
    lines, paragraphs = paragraphs_of(text)
    counted = tally(paragraphs, rules.code)
    verdict = judge(counted)
    if not verdict.judged:
        raise Unopenable(
            f"{name}: too little narration to judge: {counted.sentences} of the "
            f"{rules.minimum_sentences} sentences needed"
        )
    return Measured(name, counted, verdict, places(paragraphs, rules.code), lines)


def paragraphs_of(text: str) -> tuple[tuple[int, ...], list[str]]:
    lines: list[int] = []
    paragraphs: list[str] = []
    held: list[str] = []
    for number, line in enumerate(text.replace("\r\n", "\n").split("\n"), start=1):
        line = stripped(line)
        if line and not held:
            lines.append(number)
        if line:
            held.append(line)
        elif held:
            paragraphs.append(" ".join(held))
            held = []
    if held:
        paragraphs.append(" ".join(held))
    return tuple(lines), paragraphs


def report(one: Measured, show_places: bool, rules: Language) -> str:
    counted = one.tally
    lines = [
        one.name,
        (
            f"  narration: {plural(counted.sentences, 'sentence')} in "
            f"{plural(counted.paragraphs, 'paragraph')} "
            f"({plural(counted.dialogue_paragraphs, 'dialogue paragraph')} left out)"
        ),
        (
            f"  sentence length: mean {counted.mean:.1f} words, spread {counted.spread:.2f}, "
            f"longest {counted.longest}"
        ),
        f"  {rules.long_words} words or more: {counted.long_share:.1%}",
        (
            f"  paragraphs of {rules.uniform_low}-{rules.uniform_high} sentences: "
            f"{counted.uniform_share:.1%}"
        ),
        f"  in runs opening with the subject: {counted.subject_run_share:.1%}",
    ]
    if one.verdict.findings:
        lines.append("")
        lines.extend(f"  {described(finding, rules)}" for finding in one.verdict.findings)
    if show_places and one.runs:
        lines.append("")
        lines.extend(f"  {placed(run, one.lines)}" for run in one.runs)
    return "\n".join(lines) + "\n"


def described(finding: Finding, rules: Language) -> str:
    wanted = "want at least" if finding.bound == MIN else "want at most"
    return {
        SPREAD: (
            f"sentence lengths vary too little: spread {finding.value:.2f}, "
            f"{wanted} {finding.limit:.2f}"
        ),
        LONG_SENTENCES: (
            f"{finding.value:.1%} of sentences have {rules.long_words} words or more, "
            f"{wanted} {finding.limit:.0%}"
        ),
        UNIFORM_PARAGRAPHS: (
            f"{finding.value:.1%} of paragraphs have {rules.uniform_low}-{rules.uniform_high} "
            f"sentences, {wanted} {finding.limit:.0%}"
        ),
        SUBJECT_RUNS: (
            f"{finding.value:.1%} of sentences sit in runs of {rules.subject_run} or more "
            f"that open with their subject, {wanted} {finding.limit:.0%}"
        ),
    }[finding.kind]


def placed(run: Run, lines: tuple[int, ...]) -> str:
    text = run.sentences[0].text
    opening = f'"{text[:EXCERPT]}..."' if len(text) > EXCERPT else f'"{text}"'
    return (
        f"line {lines[run.paragraph]}: {len(run.sentences)} in a row open with their subject: "
        f"{opening}"
    )


def plural(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def parser() -> argparse.ArgumentParser:
    built = argparse.ArgumentParser(
        prog="prose-rhythm",
        description="Measure how sentence length, sentence openings and paragraph size vary "
        "in prose, and report where the rhythm goes flat. Input is plain text with "
        "paragraphs separated by blank lines.",
    )
    built.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    built.add_argument("paths", nargs="+", help="UTF-8 plain text files, or - for stdin")
    built.add_argument(
        "--language",
        default=ENGLISH,
        help=f"language of the text as a BCP 47 code (default {ENGLISH})",
    )
    built.add_argument(
        "--places",
        action="store_true",
        help="list every run of sentences opening with the subject, by the line its "
        "paragraph starts on",
    )
    return built
