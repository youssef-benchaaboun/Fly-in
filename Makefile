PYTHON := python3
VENV := .venv
MAP ?= test.txt

.PHONY: install run debug clean lint lint-strict

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install flake8 mypy

run:
	$(PYTHON) main.py $(MAP)

debug:
	$(PYTHON) -m pdb main.py $(MAP)

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .ruff_cache

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict
