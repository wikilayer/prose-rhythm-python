from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest
import yaml

from prose_rhythm import Tally, judge, places, tally
from prose_rhythm.norms import Language, language
from prose_rhythm.text import sentences_of

CORPUS = Path(__file__).parent.parent / "corpus"


def held(name: str) -> dict[str, Any]:
    return yaml.safe_load((CORPUS / name).read_text(encoding="utf-8"))


def cases(name: str) -> list[dict[str, Any]]:
    found = held(name)["cases"]
    assert found, f"{name} holds no cases, so its test cannot fail"
    return found


def rules(name: str) -> Language:
    return language(held(name)["language"])


@pytest.mark.parametrize("case", cases("sentences.yaml"), ids=lambda case: case["name"])
def test_sentences(case: dict[str, Any]) -> None:
    found = sentences_of(case["paragraph"], rules("sentences.yaml"))
    assert [[sentence.text, sentence.words] for sentence in found] == case["sentences"]


@pytest.mark.parametrize("case", cases("openings.yaml"), ids=lambda case: case["sentence"])
def test_openings(case: dict[str, Any]) -> None:
    assert rules("openings.yaml").opens_with_subject(case["sentence"]) is case["subject_first"]


@pytest.mark.parametrize("case", cases("dialogue.yaml"), ids=lambda case: case["name"])
def test_dialogue(case: dict[str, Any]) -> None:
    assert rules("dialogue.yaml").is_dialogue(case["paragraph"]) is case["dialogue"]


@pytest.mark.parametrize("case", cases("tallies.yaml"), ids=lambda case: case["name"])
def test_tallies(case: dict[str, Any]) -> None:
    code = held("tallies.yaml")["language"]
    counted = tally(case["paragraphs"], code)
    assert {key: value for key, value in asdict(counted).items() if key != "language"} == case[
        "tally"
    ]
    verdict = judge(counted)
    assert verdict.judged is case["judged"]
    assert [asdict(finding) for finding in verdict.findings] == case["findings"]
    assert [
        {"paragraph": run.paragraph, "sentences": len(run.sentences)}
        for run in places(case["paragraphs"], code)
    ] == case["places"]


@pytest.mark.parametrize("case", cases("tallies.yaml"), ids=lambda case: case["name"])
def test_tallies_add_up_paragraph_by_paragraph(case: dict[str, Any]) -> None:
    code = held("tallies.yaml")["language"]
    summed = Tally(code)
    for paragraph in case["paragraphs"]:
        summed += tally([paragraph], code)
    assert summed == tally(case["paragraphs"], code)
