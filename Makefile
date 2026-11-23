PYTHON := python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
FLAKE8 := $(VENV)/bin/flake8
MYPY := $(VENV)/bin/mypy
RUN_ARGS := $(filter-out run,$(MAKECMDGOALS))
MAP := $(or $(firstword $(RUN_ARGS)),test)

ifneq ($(filter run,$(MAKECMDGOALS)),)
ifneq ($(word 2,$(RUN_ARGS)),)
$(error Usage: make run [map_file])
endif

# An argument passed after `run` is also parsed by Make as a goal. Mark it as
# handled so Make does not print "Nothing to be done for ..." after the run.
.PHONY: $(RUN_ARGS)
$(RUN_ARGS):
	@:
endif

.PHONY: install run debug clean lint lint-strict

install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install flake8 mypy

run:
	$(PYTHON) main.py $(MAP)

debug:
	$(PYTHON) -m pdb main.py $(MAP)

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache .ruff_cache

lint:
	$(FLAKE8) .
	$(MYPY) . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(FLAKE8) .
	$(MYPY) . --strict
