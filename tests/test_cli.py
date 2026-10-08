import io
import sys
from pathlib import Path

import pytest

from prose_rhythm import __version__
from prose_rhythm.cli import CLEAN, FOUND, UNUSABLE, main

FLAT_PARAGRAPH = (
    "He climbed the stairs to the attic. The boxes stood where his father had left them.\n"
    "He opened the first one and found letters tied with string. He read the top letter by "
    "the window.\n\n"
)
VARIED_PARAGRAPHS = (
    "Rain. Under the eave the stone stayed dry, and she waited there with the basket "
    "against her hip while the carts went by one after another, each wheel striking the "
    "same broken flag and rolling on as if nothing in the street had ever been broken at all. "
    "Then quiet.\n\n"
    "When the last cart had gone she lifted the latch. Inside, nobody moved for a long "
    "while. She counted the hooks.\n\n"
    "Twice the door swung back on her. Slowly, with her shoulder, she held it.\n\n"
)
FLAT = FLAT_PARAGRAPH * 8
VARIED = VARIED_PARAGRAPHS * 4


def a_text(tmp_path: Path, text: str) -> str:
    path = tmp_path / "chapter.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def piped(monkeypatch: pytest.MonkeyPatch, data: bytes) -> None:
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(data), encoding="latin-1"))


def test_flat_prose_is_found(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([a_text(tmp_path, FLAT), "--places"]) == FOUND
    out = capsys.readouterr().out
    assert "sentence lengths vary too little: spread 0.17, want at least 0.55" in out
    assert "0.0% of sentences have 30 words or more, want at least 4%" in out
    assert "100.0% of paragraphs have 4-6 sentences, want at most 50%" in out
    assert "100.0% of sentences sit in runs of 4 or more that open with their subject" in out
    assert (
        'line 4: 4 in a row open with their subject: "He climbed the stairs to the attic."' in out
    )


def test_varied_prose_is_clean(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([a_text(tmp_path, VARIED)]) == CLEAN, capsys.readouterr().out


def test_stdin_is_read_as_utf8(monkeypatch: pytest.MonkeyPatch) -> None:
    piped(monkeypatch, ("“Yes,” she said.\n\n" + VARIED).encode("utf-8"))
    assert main(["-"]) == CLEAN


def test_stdin_twice_is_unusable(monkeypatch: pytest.MonkeyPatch) -> None:
    piped(monkeypatch, VARIED.encode("utf-8"))
    assert main(["-", "-"]) == UNUSABLE


def test_version_names_the_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["--version"])
    assert capsys.readouterr().out.strip() == f"prose-rhythm {__version__}"


def test_an_unknown_language_is_unusable(tmp_path: Path) -> None:
    assert main([a_text(tmp_path, VARIED), "--language", "xx"]) == UNUSABLE


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(None, id="missing file"),
        pytest.param("Café crème. ".encode("latin-1") * 40, id="not utf-8"),
        pytest.param(b"", id="empty"),
        pytest.param(b'"Now," she said.\n', id="dialogue only"),
        pytest.param(b"She went home. It was late.\n", id="too little narration"),
    ],
)
def test_unmeasurable_input_is_unusable(tmp_path: Path, content: bytes | None) -> None:
    path = tmp_path / "chapter.txt"
    if content is not None:
        path.write_bytes(content)
    assert main([str(path)]) == UNUSABLE


def test_crlf_line_endings_read_like_lf(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    main([a_text(tmp_path, FLAT), "--places"])
    unix = capsys.readouterr().out
    main([a_text(tmp_path, FLAT.replace("\n", "\r\n")), "--places"])
    assert capsys.readouterr().out == unix
