import unicodedata
from dataclasses import dataclass
from functools import cache
from importlib.resources import files

import yaml

PACKAGE = "prose_rhythm"
RULES = "rhythm.yaml"
SPACES = "\t\n\v\f\r \x85"
SPACE_CATEGORIES = ("Zs", "Zl", "Zp")
MIN = "min"
MAX = "max"
SPREAD = "spread"
LONG_SENTENCES = "long_sentences"
UNIFORM_PARAGRAPHS = "uniform_paragraphs"
SUBJECT_RUNS = "subject_runs"
KINDS = (SPREAD, LONG_SENTENCES, UNIFORM_PARAGRAPHS, SUBJECT_RUNS)
LANGUAGE_KEYS = {
    "thresholds",
    "checks",
    "word_joiners",
    "sentence_ends",
    "closers",
    "openers",
    "quote_pairs",
    "dialogue_quoted_share",
    "initial_exceptions",
    "abbreviations",
    "non_subject_suffixes",
    "subject_despite_suffix",
    "non_subject_openers",
}
THRESHOLD_KEYS = {"minimum_sentences", "long_words", "uniform_paragraph_sentences", "subject_run"}
CHECK_KEYS = {"kind", "bound", "limit"}


class Unreadable(Exception):
    pass


class UnknownLanguage(Exception):
    pass


def is_space(character: str) -> bool:
    return character in SPACES or unicodedata.category(character) in SPACE_CATEGORIES


def is_word(character: str) -> bool:
    return unicodedata.category(character)[0] in "LN"


def is_mark(character: str) -> bool:
    return unicodedata.category(character)[0] == "M"


def is_upper(character: str) -> bool:
    return unicodedata.category(character) == "Lu"


def is_decimal(character: str) -> bool:
    return unicodedata.category(character) == "Nd"


def lowered(word: str) -> str:
    return "".join(character.lower()[0] for character in word)


def stripped(text: str) -> str:
    start = 0
    end = len(text)
    while start < end and is_space(text[start]):
        start += 1
    while end > start and is_space(text[end - 1]):
        end -= 1
    return text[start:end]


@dataclass(frozen=True)
class Check:
    kind: str
    bound: str
    limit: float

    def fails(self, value: float) -> bool:
        return value < self.limit if self.bound == MIN else value > self.limit


@dataclass(frozen=True)
class Language:
    code: str
    minimum_sentences: int
    long_words: int
    uniform_low: int
    uniform_high: int
    subject_run: int
    checks: tuple[Check, ...]
    word_joiners: str
    sentence_ends: str
    closers: str
    openers: str
    quote_pairs: tuple[tuple[str, str], ...]
    dialogue_quoted_share: float
    abbreviations: frozenset[str]
    initial_exceptions: frozenset[str]
    non_subject_openers: frozenset[str]
    non_subject_suffixes: tuple[str, ...]
    subject_despite_suffix: frozenset[str]

    def words(self, text: str) -> list[str]:
        found: list[str] = []
        word = ""
        for character in text + " ":
            continues = character in self.word_joiners or is_mark(character)
            if is_word(character) or (word and continues):
                word += character
            elif word:
                found.append(word.rstrip(self.word_joiners))
                word = ""
        return found

    def sentence_breaks(self, paragraph: str) -> list[int]:
        found: list[int] = []
        end = len(paragraph)
        position = 0
        while position < end:
            if paragraph[position] not in self.sentence_ends:
                position += 1
                continue
            while position < end and paragraph[position] in self.sentence_ends:
                position += 1
            while position < end and paragraph[position] in self.closers:
                position += 1
            space = position
            while space < end and is_space(paragraph[space]):
                space += 1
            if space > position:
                found.append(space)
                position = space
        return found

    def opens_with_subject(self, sentence: str) -> bool:
        words = self.words(sentence)
        if not words:
            return False
        first = lowered(words[0])
        if first in self.non_subject_openers:
            return False
        if first in self.subject_despite_suffix:
            return True
        return not first.endswith(self.non_subject_suffixes)

    def stops_short(self, sentence: str) -> bool:
        last = sentence[last_word_start(sentence) :].rstrip(self.closers).lstrip(self.openers)
        if last in self.abbreviations:
            return True
        initial = len(last) == 2 and is_upper(last[0]) and last[1] == "."
        return initial and last not in self.initial_exceptions

    def begins_sentence(self, text: str) -> bool:
        first = text[:1]
        return not first or is_upper(first) or is_decimal(first) or first in self.openers

    def is_dialogue(self, paragraph: str) -> bool:
        if not paragraph:
            return False
        quoted = sum(quoted_length(paragraph, *pair) for pair in self.quote_pairs)
        return quoted / len(paragraph) >= self.dialogue_quoted_share


def last_word_start(text: str) -> int:
    position = len(text)
    while position > 0 and not is_space(text[position - 1]):
        position -= 1
    return position


def quoted_length(text: str, opening: str, closing: str) -> int:
    total = 0
    position = 0
    while True:
        start = text.find(opening, position)
        while start > 0 and is_word(text[start - 1]):
            start = text.find(opening, start + 1)
        if start == -1:
            return total
        end = text.find(closing, start + len(opening))
        while end != -1 and word_follows(text, end + len(closing)):
            end = text.find(closing, end + 1)
        if end == -1:
            return total
        position = end + len(closing)
        total += position - start


def word_follows(text: str, position: int) -> bool:
    return position < len(text) and is_word(text[position])


def exactly(written: dict, keys: set[str], where: str) -> dict:
    if set(written) != keys:
        missing = ", ".join(sorted(keys - set(written))) or "nothing"
        unknown = ", ".join(sorted(set(written) - keys)) or "nothing"
        raise ValueError(f"{where}: missing {missing}, unknown {unknown}")
    return written


def check_of(code: str, written: dict) -> Check:
    exactly(written, CHECK_KEYS, f"{code} check")
    check = Check(str(written["kind"]), str(written["bound"]), float(written["limit"]))
    if check.kind not in KINDS:
        raise ValueError(f"{code}: no check is called {check.kind!r}")
    if check.bound not in (MIN, MAX):
        raise ValueError(f"{code}: {check.kind} is bound by neither {MIN} nor {MAX}")
    return check


def language_of(code: str, written: dict) -> Language:
    exactly(written, LANGUAGE_KEYS, code)
    limits = exactly(written["thresholds"], THRESHOLD_KEYS, f"{code} thresholds")
    uniform_low, uniform_high = limits["uniform_paragraph_sentences"]
    checks = tuple(check_of(code, check) for check in written["checks"])
    return Language(
        code=code,
        minimum_sentences=int(limits["minimum_sentences"]),
        long_words=int(limits["long_words"]),
        uniform_low=int(uniform_low),
        uniform_high=int(uniform_high),
        subject_run=int(limits["subject_run"]),
        checks=checks,
        word_joiners=str(written["word_joiners"]),
        sentence_ends=str(written["sentence_ends"]),
        closers=str(written["closers"]),
        openers=str(written["openers"]),
        quote_pairs=tuple(
            (str(opening), str(closing)) for opening, closing in written["quote_pairs"]
        ),
        dialogue_quoted_share=float(written["dialogue_quoted_share"]),
        abbreviations=frozenset(written["abbreviations"]),
        initial_exceptions=frozenset(written["initial_exceptions"]),
        non_subject_openers=frozenset(written["non_subject_openers"]),
        non_subject_suffixes=tuple(written["non_subject_suffixes"]),
        subject_despite_suffix=frozenset(written["subject_despite_suffix"]),
    )


@cache
def languages() -> dict[str, Language]:
    try:
        written = yaml.safe_load(files(PACKAGE).joinpath(RULES).read_text(encoding="utf-8"))
        return {
            str(code): language_of(str(code), language)
            for code, language in written["languages"].items()
        }
    except (KeyError, TypeError, ValueError, AttributeError, yaml.YAMLError) as failure:
        raise Unreadable(f"{RULES}: {failure!r}") from failure


def language(code: str) -> Language:
    known = languages()
    if code not in known:
        raise UnknownLanguage(
            f"no rules for language {code!r}, only for {', '.join(sorted(known))}"
        )
    return known[code]
