# Makefile for llmXive ZPPPO Extension
# Provides shortcuts for common development tasks

.PHONY: install lint format test clean

# Install dependencies
install:
    pip install -e ".[dev]"
    pre-commit install

# Run linter (ruff)
lint:
    ruff check .

# Run formatter (ruff format or black)
format:
    ruff format .
    # If using black: black .

# Run tests
test:
    pytest tests/ -v

# Run full CI checks (lint + format + test)
ci: lint format test

# Clean build artifacts
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    find . -type d -name ".pytest_cache" -exec rm -rf {} +
    find . -type d -name ".ruff_cache" -exec rm -rf {} +
    find . -type d -name "build" -exec rm -rf {} +
    find . -type d -name "dist" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    rm -rf .coverage htmlcov/