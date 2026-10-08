import copy
from collections.abc import Callable
from importlib.resources import files
from typing import Any

import pytest
import yaml

from prose_rhythm import places, tally
from prose_rhythm.norms import language_of

WRITTEN = yaml.safe_load(files("prose_rhythm").joinpath("rhythm.yaml").read_text("utf-8"))


def english() -> dict[str, Any]:
    return copy.deepcopy(WRITTEN["languages"]["en"])


def test_the_rules_as_shipped_load() -> None:
    assert language_of("en", english()).code == "en"


@pytest.mark.parametrize(
    "spoil",
    [
        pytest.param(lambda rules: rules.update(spelling="en-GB"), id="unknown key"),
        pytest.param(lambda rules: rules.pop("openers"), id="missing key"),
        pytest.param(lambda rules: rules["thresholds"].update(long=30), id="unknown threshold"),
        pytest.param(lambda rules: rules["checks"][0].update(kind="spreed"), id="unknown check"),
        pytest.param(lambda rules: rules["checks"][0].update(bound="least"), id="unknown bound"),
    ],
)
def test_rules_a_port_would_refuse_are_refused(
    spoil: Callable[[dict[str, Any]], object],
) -> None:
    rules = english()
    spoil(rules)
    with pytest.raises(ValueError):
        language_of("en", rules)


@pytest.mark.parametrize("call", [tally, places])
def test_one_string_is_not_taken_for_a_list_of_paragraphs(call: Callable[[str], object]) -> None:
    with pytest.raises(TypeError):
        call("He ran. She ran.")
