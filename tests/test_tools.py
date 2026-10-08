import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from prose import plain

CASES = yaml.safe_load((Path(__file__).parent / "data" / "markdown.yaml").read_text("utf-8"))


@pytest.mark.parametrize("case", CASES["cases"], ids=lambda case: case["name"])
def test_each_paragraph_stays_on_its_line_and_nothing_else_is_kept(case: dict[str, Any]) -> None:
    lines = plain(case["source"]).split("\n")
    kept = [[number, line] for number, line in enumerate(lines, start=1) if line]
    assert kept == case["paragraphs"]
