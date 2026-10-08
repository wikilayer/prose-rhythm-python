import math
from collections.abc import Iterable
from dataclasses import dataclass, fields

from .norms import (
    LONG_SENTENCES,
    SPREAD,
    SUBJECT_RUNS,
    UNIFORM_PARAGRAPHS,
    Language,
    language,
)
from .text import Sentence, sentences_of

ENGLISH = "en"


class MixedLanguages(Exception):
    pass


@dataclass(frozen=True)
class Tally:
    language: str
    sentences: int = 0
    words: int = 0
    squared_words: int = 0
    long_sentences: int = 0
    longest: int = 0
    paragraphs: int = 0
    uniform_paragraphs: int = 0
    subject_run_sentences: int = 0
    dialogue_paragraphs: int = 0

    def __add__(self, other: "Tally") -> "Tally":
        if other.language != self.language:
            raise MixedLanguages(f"cannot add a {other.language} tally to a {self.language} one")
        summed = {
            field.name: getattr(self, field.name) + getattr(other, field.name)
            for field in fields(self)
            if field.name not in ("language", "longest")
        }
        return Tally(self.language, longest=max(self.longest, other.longest), **summed)

    @property
    def mean(self) -> float:
        return self.words / self.sentences if self.sentences else 0.0

    @property
    def spread(self) -> float:
        if not self.words:
            return 0.0
        return math.sqrt(self.sentences * self.squared_words - self.words**2) / self.words

    @property
    def long_share(self) -> float:
        return self.long_sentences / self.sentences if self.sentences else 0.0

    @property
    def uniform_share(self) -> float:
        return self.uniform_paragraphs / self.paragraphs if self.paragraphs else 0.0

    @property
    def subject_run_share(self) -> float:
        return self.subject_run_sentences / self.sentences if self.sentences else 0.0

    def metric(self, kind: str) -> float:
        return {
            SPREAD: self.spread,
            LONG_SENTENCES: self.long_share,
            UNIFORM_PARAGRAPHS: self.uniform_share,
            SUBJECT_RUNS: self.subject_run_share,
        }[kind]


@dataclass(frozen=True)
class Finding:
    kind: str
    value: float
    bound: str
    limit: float


@dataclass(frozen=True)
class Verdict:
    judged: bool
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class Run:
    paragraph: int
    sentences: tuple[Sentence, ...]


def tally(paragraphs: Iterable[str], language_code: str = ENGLISH) -> Tally:
    refuse_single_text(paragraphs)
    rules = language(language_code)
    total = Tally(rules.code)
    for paragraph in paragraphs:
        total += paragraph_tally(paragraph, rules)
    return total


def judge(counted: Tally) -> Verdict:
    rules = language(counted.language)
    if counted.sentences < rules.minimum_sentences:
        return Verdict(judged=False, findings=())
    findings = tuple(
        Finding(check.kind, counted.metric(check.kind), check.bound, check.limit)
        for check in rules.checks
        if check.fails(counted.metric(check.kind))
    )
    return Verdict(judged=True, findings=findings)


def refuse_single_text(paragraphs: Iterable[str]) -> None:
    if isinstance(paragraphs, str):
        raise TypeError("paragraphs must be a list of strings, not one string")


def places(paragraphs: Iterable[str], language_code: str = ENGLISH) -> tuple[Run, ...]:
    refuse_single_text(paragraphs)
    rules = language(language_code)
    found: list[Run] = []
    for index, paragraph in enumerate(paragraphs):
        if rules.is_dialogue(paragraph):
            continue
        found.extend(Run(index, run) for run in subject_runs(sentences_of(paragraph, rules), rules))
    return tuple(found)


def paragraph_tally(paragraph: str, rules: Language) -> Tally:
    if rules.is_dialogue(paragraph):
        return Tally(rules.code, dialogue_paragraphs=1)
    sentences = sentences_of(paragraph, rules)
    if not sentences:
        return Tally(rules.code)
    lengths = [sentence.words for sentence in sentences]
    return Tally(
        rules.code,
        sentences=len(lengths),
        words=sum(lengths),
        squared_words=sum(length * length for length in lengths),
        long_sentences=sum(length >= rules.long_words for length in lengths),
        longest=max(lengths),
        paragraphs=1,
        uniform_paragraphs=int(rules.uniform_low <= len(lengths) <= rules.uniform_high),
        subject_run_sentences=sum(len(run) for run in subject_runs(sentences, rules)),
    )


def subject_runs(sentences: tuple[Sentence, ...], rules: Language) -> list[tuple[Sentence, ...]]:
    found: list[tuple[Sentence, ...]] = []
    run: list[Sentence] = []
    for sentence in (*sentences, None):
        if sentence is not None and rules.opens_with_subject(sentence.text):
            run.append(sentence)
            continue
        if len(run) >= rules.subject_run:
            found.append(tuple(run))
        run = []
    return found
