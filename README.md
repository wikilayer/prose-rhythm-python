# prose-rhythm

[![Tests](https://github.com/wikilayer/prose-rhythm-python/actions/workflows/tests.yml/badge.svg)](https://github.com/wikilayer/prose-rhythm-python/actions/workflows/tests.yml)
[![Documentation](https://github.com/wikilayer/prose-rhythm-python/actions/workflows/documentation.yml/badge.svg)](https://wikilayer.github.io/prose-rhythm-python/prose_rhythm.html)

Measures how sentence rhythm varies in prose and says where it goes flat.

Writers alternate short, middle and long sentences, start them in different
ways and let paragraphs grow and shrink. Text where every sentence runs ten
to fifteen words, opens with its subject and sits in a paragraph of four or
five such sentences reads as stamped out, and that evenness is one of the
plainest signs of machine-written prose.

This is the leading port. The [Go port](https://github.com/wikilayer/prose-rhythm)
reads the same rules and answers the same test cases; matching major and minor
versions promise the same counts.

## Installing

Requires Python 3.11 or newer.

```sh
python -m pip install git+https://github.com/wikilayer/prose-rhythm-python.git@v0.3.0
```

## Using

The library takes plain text: a list of paragraphs, already free of markup.
It counts them into a `Tally`, and tallies add up, so a section, a chapter and
a whole book are counted the same way and judged once.

```python
>>> from prose_rhythm import judge, places, tally
>>> flat = ("He climbed the stairs to the attic. The boxes stood where his father "
...         "had left them. He opened the first one and found letters tied with string. "
...         "He read the top letter by the window.")
>>> counted = tally([flat] * 4) + tally([flat] * 4)
>>> counted.sentences, counted.words, round(counted.spread, 2)
(32, 280, 0.17)
>>> [finding.kind for finding in judge(counted).findings]
['spread', 'long_sentences', 'uniform_paragraphs', 'subject_runs']
>>> judge(tally([flat])).judged
False
>>> [(run.paragraph, len(run.sentences)) for run in places([flat, "Rain."])]
[(0, 4)]

```

`judge` leaves a text of fewer than 30 sentences of narration unjudged
rather than guessing. `places` names the paragraphs holding a run of
sentences that open with their subject, by their index in the list given.

## What it measures

Only narration counts: a paragraph is dialogue, and is left out, when at
least a fifth of it stands inside quotation marks.

| Finding | Measure | Wanted |
|---|---|---|
| `spread` | standard deviation of sentence length over its mean | at least 0.55 |
| `long_sentences` | share of sentences of 30 words or more | at least 4% |
| `uniform_paragraphs` | share of paragraphs of four to six sentences | at most 50% |
| `subject_runs` | share of sentences in runs of four or more, within a paragraph, whose first word is not a preposition, conjunction or adverb from the list and does not end in *-ing* or *-ly*, save listed words such as *morning* or *only* | at most 40% |

The spread is computed from integer sums, `sqrt(n·Σx² − (Σx)²) / Σx`, so that
every port gets the same bits.

The checks, their limits and each language's word lists and typography are
data in [`rhythm.yaml`](https://github.com/wikilayer/prose-rhythm-python/blob/main/src/prose_rhythm/rhythm.yaml),
keyed by BCP 47 code. English is the only language so far; asking for another
raises `UnknownLanguage`.

## Command line

`prose-rhythm` reads UTF-8 plain text with paragraphs separated by blank lines
and exits 0 when nothing is found, 1 when something is, and 2 when the input
cannot be judged.

```
$ prose-rhythm chapter.txt --places
chapter.txt
  narration: 32 sentences in 8 paragraphs (0 dialogue paragraphs left out)
  sentence length: mean 8.8 words, spread 0.17, longest 11
  30 words or more: 0.0%
  paragraphs of 4-6 sentences: 100.0%
  in runs opening with the subject: 100.0%

  sentence lengths vary too little: spread 0.17, want at least 0.55
  0.0% of sentences have 30 words or more, want at least 4%
  100.0% of paragraphs have 4-6 sentences, want at most 50%
  100.0% of sentences sit in runs of 4 or more that open with their subject, want at most 40%

  line 1: 4 in a row open with their subject: "He climbed the stairs to the attic."
  line 3: 4 in a row open with their subject: "He climbed the stairs to the attic."
  ...
```

Markdown and Project Gutenberg texts go through
[`tools/prose.py`](https://github.com/wikilayer/prose-rhythm-python/blob/main/tools/prose.py)
first. It keeps each paragraph on the line it started on, so places point
into the original file:

```sh
python tools/prose.py chapter.md | prose-rhythm - --places
```

`-` in place of the file reads the source from stdin.

## Shared rules and cases

[`rhythm.yaml`](https://github.com/wikilayer/prose-rhythm-python/blob/main/src/prose_rhythm/rhythm.yaml)
and the cases in [`corpus/`](https://github.com/wikilayer/prose-rhythm-python/tree/main/corpus)
are the originals; `make sync-corpus` copies them into the other ports checked
out next to this one. `tallies.yaml` keeps its sample paragraphs under
`anchors` and refers to them by YAML alias. A new case is written here once and asked of every port.

`corpus/novels.yaml` records the counts of eight public-domain fantasy and
science fiction novels from Project Gutenberg, none of which may have a
finding. `make measure` downloads them into `data/` and checks both. The texts
are not committed.

## Lines of Code

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/wikilayer/prose-rhythm-python/main/.github/loc-history-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/wikilayer/prose-rhythm-python/main/.github/loc-history-light.svg">
  <img alt="Lines of Code graph" src="https://raw.githubusercontent.com/wikilayer/prose-rhythm-python/main/.github/loc-history-light.svg">
</picture>
