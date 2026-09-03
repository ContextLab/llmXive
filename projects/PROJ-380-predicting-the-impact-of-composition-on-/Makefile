.PHONY: all install lint format test clean

# Default target
all: lint format test

install:
	pip install -e ".[dev]"

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
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache htmlcov .coverage
	rm -rf data/processed/* data/artifacts/*
	rm -rf artifacts/*
	rm -rf build dist