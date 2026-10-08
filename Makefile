.DEFAULT_GOAL := build

.PHONY: install install-tools link-markdown format comments lint test-build test docs build data measure sync-corpus

PORTS := ../prose-rhythm
SHARED := corpus/sentences.yaml corpus/openings.yaml corpus/dialogue.yaml corpus/tallies.yaml corpus/novels.yaml

install:
	python -m pip install -r requirements.txt
	python -m pip install --no-deps -e .

install-tools:
	python -m pip install --upgrade git+https://github.com/botforge-pro/commentcensor.git

link-markdown:
	mkdir -p $(HOME)/.local/bin
	ln -sf $(CURDIR)/tools/prose-rhythm-md $(HOME)/.local/bin/prose-rhythm-md

format:
	python -m ruff check --fix src tests tools
	python -m ruff format src tests tools

comments:
	commentcensor .

lint: comments
	python -m ruff check src tests tools
	python -m ruff format --check src tests tools

test-build:
	python -m compileall -q src tests tools

test:
	python -m pytest -q $(TEST)

docs:
	python -m pdoc prose_rhythm -o build/docs

build: lint test-build test docs
	python -m build

data:
	mkdir -p data
	for id in $$(awk '/^  - id:/{print $$3}' corpus/novels.yaml); do \
		test -s data/$$id.txt && continue; \
		curl -sfL https://www.gutenberg.org/cache/epub/$$id/pg$$id.txt -o data/$$id.txt \
			|| { echo "$$id: download failed"; rm -f data/$$id.txt; exit 1; }; \
	done

measure: data
	python -m pytest -q -o addopts= tests/novels

sync-corpus:
	cp src/prose_rhythm/rhythm.yaml $(PORTS)/rhythm.yaml
	mkdir -p $(PORTS)/corpus
	cp $(SHARED) $(PORTS)/corpus/
