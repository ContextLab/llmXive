.PHONY: all lint format test clean setup

# Default target
all: lint format test

# Install dependencies
setup:
	pip install -r requirements.txt

# Run linter (ruff)
lint:
	ruff check code/

# Fix linting issues automatically
lint-fix:
	ruff check --fix code/

# Format code (black)
format:
	black code/

# Check formatting without modifying
format-check:
	black --check code/

# Run tests
test:
	pytest tests/ -v --cov=code --cov-report=term-missing

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf data/processed/*
	rm -rf data/artifacts/*
	rm -rf artifacts/*

# Run full pipeline
run-pipeline:
	python code/benchmark_pipeline.py
