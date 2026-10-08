# Changelog

Notable changes to `prose-rhythm` are documented here in the format of
[Keep a Changelog](https://keepachangelog.com/). This Python package leads the
shared rules and cases consumed by the Go port; matching major and minor versions
promise the same counts on those cases.

The package remains below 1.0 while its public API is settling.

## 0.3.0 - 2026-10-08

### Fixed

- The words *on* and *off* open a sentence that does not start with its
  subject. YAML 1.1 read them as booleans, so they never matched; they are
  quoted now, and rules whose word lists hold anything but strings are refused.
  The recorded counts of five reference novels drop by a few sentences in runs.

### Added

- `corpus/openings.yaml` gained sentences opening with *On* and *Off*.

## 0.2.0 - 2026-10-08

The first public release.

### Added

- `tally(paragraphs, language)` counts a list of plain-text paragraphs into a
  `Tally` of integers. Tallies add up with `+`, so any part of a text and the
  whole are counted the same way; adding tallies of different languages raises
  `MixedLanguages`.
- `judge(tally)` returns a `Verdict`: unjudged below 30 sentences of narration,
  otherwise the failed checks as `Finding(kind, value, bound, limit)`.
- `places(paragraphs, language)` names the paragraphs holding a run of
  sentences that open with their subject, by index.
- Rules are keyed by BCP 47 language code; an unknown code raises
  `UnknownLanguage`. The checks, their bounds and limits are data in
  `rhythm.yaml`.
- `corpus/` holds the cases every port answers: sentence breaks, sentence
  openings, dialogue, tallies and verdicts, and the recorded counts of the eight
  reference novels.
- `tools/prose.py` turns Markdown or a Project Gutenberg text into plain
  paragraphs, keeping each on the line it started on.

### Changed

- The library reads plain text only. Markdown, front matter, headings, lists,
  code and emphasis are the caller's to remove, and `prose-rhythm` reads plain
  text with paragraphs separated by blank lines.
- The spread is computed from integer sums, so every port gets the same bits.
- An underscore is no longer part of a word, and a joiner such as a trailing
  apostrophe no longer ends one.
- Letters, digits, case and spaces are told by Unicode category rather than by
  ASCII patterns, so words in any script count.

### Removed

- The share of sentences opening with their subject and the runs of sentences
  of nearly equal length: both were reported and never judged.

## 0.1.0 - 2026-10-08

A private first version that measured Markdown files and reported the same four
findings.
