import doctest
from pathlib import Path

README = Path(__file__).parent.parent / "README.md"


def test_readme_examples_run_as_written() -> None:
    result = doctest.testfile(str(README), module_relative=False, optionflags=doctest.ELLIPSIS)
    assert result.attempted, "README holds no examples, so this test cannot fail"
    assert result.failed == 0
