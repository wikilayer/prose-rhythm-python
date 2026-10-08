from dataclasses import dataclass

from .norms import Language, stripped


@dataclass(frozen=True)
class Sentence:
    text: str
    words: int


def sentences_of(paragraph: str, language: Language) -> tuple[Sentence, ...]:
    texts: list[str] = []
    start = 0
    for end in language.sentence_breaks(paragraph):
        candidate = stripped(paragraph[start:end])
        if language.stops_short(candidate) or not language.begins_sentence(paragraph[end:]):
            continue
        texts.append(candidate)
        start = end
    texts.append(stripped(paragraph[start:]))
    sentences = (Sentence(text, len(language.words(text))) for text in texts)
    return tuple(sentence for sentence in sentences if sentence.words)
