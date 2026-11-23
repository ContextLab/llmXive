# Makefile for llmXive MobileForge Follow-up
# Provides convenient shortcuts for linting, formatting, and testing

.PHONY: help lint format test clean install

# Default target
help:
	@echo "Available targets:"
	@echo "  make lint    - Run ruff to check code style and imports"
	@echo "  make format  - Run black to format code"
	@echo "  make check   - Run both lint and format checks (no modifications)"
	@echo "  make test    - Run pytest"
	@echo "  make install - Install dependencies"
	@echo "  make clean   - Remove temporary files"

# Install dependencies
install:
	pip install -r code/requirements.txt

# Run ruff linter (checks only, does not fix)
lint:
	cd code && ruff check .

# Run ruff linter (fixes auto-fixable issues)
lint-fix:
	cd code && ruff check . --fix

# Format code with black
format:
	cd code && black .

# Check formatting without modifying (for CI)
check-format:
	cd code && black . --check

# Run all checks (lint + format check)
check: lint check-format
	@echo "All checks passed!"

# Run tests
test:
	cd code && pytest tests/ -v

# Clean temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf .pytest_cache htmlcov .coverage