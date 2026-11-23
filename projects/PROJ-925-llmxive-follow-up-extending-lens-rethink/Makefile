# Makefile for llmXive follow-up project
# Provides convenient commands for linting, formatting, and testing

.PHONY: install lint format check lint-check format-check test clean

# Install dependencies including dev tools
install:
    pip install -r requirements.txt
    pip install -e ".[dev]"

# Run Black formatter
format:
    black code/ tests/ specs/

# Run Ruff linter with autofix
lint:
    ruff check --fix code/ tests/ specs/

# Check linting without fixing (for CI)
lint-check:
    ruff check code/ tests/ specs/

# Check formatting without changing (for CI)
format-check:
    black --check code/ tests/ specs/

# Run all checks (lint + format)
check: lint-check format-check

# Run tests
test:
    pytest code/tests/ -v

# Run tests with coverage
test-cov:
    pytest code/tests/ -v --cov=code --cov-report=term-missing

# Clean up generated files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type d -name ".pytest_cache" -exec rm -rf {} +
    find . -type d -name ".ruff_cache" -exec rm -rf {} +
    rm -rf .coverage coverage.xml htmlcov/

# Default target
all: check test