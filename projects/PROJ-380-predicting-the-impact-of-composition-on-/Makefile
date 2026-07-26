# Makefile for llmXive Project 380
# Orchestration entry point for the research pipeline

.PHONY: help lint format test clean install all

# Configuration
PYTHON := python
PIP := pip
VENV := .venv

help:
	@echo "Available targets:"
	@echo "  install    - Install dependencies (including dev tools)"
	@echo "  lint       - Run Ruff linter"
	@echo "  format     - Run Black formatter"
	@echo "  test       - Run pytest"
	@echo "  clean      - Remove temporary files and caches"
	@echo "  all        - Run lint, format, and test"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -e ".[dev]"

lint:
	ruff check code/ tests/

format:
	black code/ tests/
	ruff check --fix code/ tests/

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf .venv
	rm -rf build dist *.egg-info

all: lint format test