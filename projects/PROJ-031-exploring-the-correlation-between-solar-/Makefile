# Makefile for PROJ-031: Solar Flare & Geomagnetic Storm Correlation
# Provides convenient shortcuts for linting, formatting, and testing.

.PHONY: help lint format test clean install

# Default target
help:
	@echo "Available targets:"
	@echo "  make install  - Install dependencies from requirements.txt"
	@echo "  make lint     - Run linters (flake8, pylint) to check code style"
	@echo "  make format   - Run formatters (black, isort) to fix code style"
	@echo "  make check    - Run lint and format check (lint only)"
	@echo "  make test     - Run pytest unit tests"
	@echo "  make clean    - Remove Python cache and build artifacts"
	@echo "  make all      - Run lint, test, and format checks"

install:
	pip install -r requirements.txt

lint:
	python code/config/linting.py check

format:
	python code/config/linting.py fix

check: lint

test:
	pytest tests/ -v --tb=short

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.pyc" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build dist *.egg-info

all: lint test
	@echo "✅ All checks passed."