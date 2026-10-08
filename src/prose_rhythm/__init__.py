from .measure import (
    LONG_SENTENCES,
    SPREAD,
    SUBJECT_RUNS,
    UNIFORM_PARAGRAPHS,
    Finding,
    MixedLanguages,
    Run,
    Tally,
    Verdict,
    judge,
    places,
    tally,
)
from .norms import MAX, MIN, UnknownLanguage, Unreadable
from .text import Sentence

__version__ = "0.2.0"

__all__ = [
    "LONG_SENTENCES",
    "MAX",
    "MIN",
    "SPREAD",
    "SUBJECT_RUNS",
    "UNIFORM_PARAGRAPHS",
    "Finding",
    "MixedLanguages",
    "Run",
    "Sentence",
    "Tally",
    "UnknownLanguage",
    "Unreadable",
    "Verdict",
    "judge",
    "places",
    "tally",
]
