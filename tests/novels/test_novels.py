import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from prose import plain

from prose_rhythm import judge, tally
from prose_rhythm.cli import paragraphs_of

HELD = yaml.safe_load((ROOT / "corpus" / "novels.yaml").read_text(encoding="utf-8"))


@pytest.mark.parametrize("novel", HELD["novels"], ids=lambda novel: novel["title"])
def test_every_novel_counts_as_recorded_and_passes(novel: dict[str, Any]) -> None:
    path = ROOT / "data" / f"{novel['id']}.txt"
    assert path.exists(), f"{path} is missing; run make data"
    _, paragraphs = paragraphs_of(plain(path.read_text(encoding="utf-8-sig")))
    counted = tally(paragraphs, HELD["language"])
    assert {key: value for key, value in asdict(counted).items() if key != "language"} == novel[
        "tally"
    ]
    verdict = judge(counted)
    assert verdict.judged
    assert verdict.findings == ()
