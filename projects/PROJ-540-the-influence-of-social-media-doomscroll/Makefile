# Makefile for linting and formatting
PYTHON := python3
PROJECT_ROOT := $(shell pwd)

.PHONY: lint format check lint-fix check-isort check-black check-flake8

# Check all code quality standards
check: check-isort check-black check-flake8
	@echo ""
	@echo "✅ All checks passed!"

# Run isort in check mode
check-isort:
	@echo "Checking import order with isort..."
	$(PYTHON) -m isort --check-only --profile black code/ tests/

# Run black in check mode
check-black:
	@echo "Checking code formatting with black..."
	$(PYTHON) -m black --check --line-length 88 code/ tests/

# Run flake8
check-flake8:
	@echo "Running flake8..."
	$(PYTHON) -m flake8 --max-line-length=88 --extend-ignore=E203,W503 --select=E,F,W,C code/ tests/

# Format all code
format:
	@echo "Formatting code..."
	$(PYTHON) -m isort --profile black code/ tests/
	$(PYTHON) -m black --line-length 88 code/ tests/
	@echo "✅ Code formatted!"

# Lint and fix issues
lint-fix: format
	@echo "✅ Issues fixed!"

# Install development dependencies
install-dev:
	$(PYTHON) -m pip install -r requirements-dev.txt
	@echo "✅ Development dependencies installed!"

# Run all checks before committing (pre-commit hook simulation)
pre-commit: check
	@echo "✅ Pre-commit checks passed!"
