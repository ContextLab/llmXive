# Makefile for PROJ-080
# Provides convenient commands for linting, formatting, and testing

.PHONY: lint format check lint-fix format-fix test clean

# Linting with Ruff
lint:
	ruff check .

# Fix linting issues automatically
lint-fix:
	ruff check --fix .

# Formatting with Black
format:
	black code/ tests/

# Check formatting without modifying files
format-check:
	black --check code/ tests/

# Full formatting with Ruff format
format-full:
	ruff format . && black code/ tests/

# Full linting check (Ruff + Black)
check:
	ruff check . && black --check code/ tests/ && ruff format --check .

# Fix all issues (lint + format)
fix:
	ruff check --fix . && black code/ tests/ && ruff format .

# Run tests
test:
	py pytest -v --cov=code tests/

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

# Default target
default: check