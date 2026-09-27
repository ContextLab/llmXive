# Makefile for PROJ-405 Development Tasks
# Provides shortcuts for linting, formatting, and testing

.PHONY: help lint format format-check test clean install-dev

PYTHON := python3
VENV := venv

help: ## Show this help message
@echo "Usage: make [target]"
@echo ""
@echo "Targets:"
@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install-dev: ## Install development dependencies
$(PYTHON) -m pip install --upgrade pip
$(PYTHON) -m pip install -e ".[dev]"

lint: ## Run linters (ruff and flake8)
@echo "Running Ruff..."
$(PYTHON) -m ruff check code/ tests/
@echo "Running Flake8..."
$(PYTHON) -m flake8 code/ tests/
@echo "Linting complete."

format: ## Format code with Black and sort imports with Ruff
@echo "Formatting code with Black..."
$(PYTHON) -m black code/ tests/
@echo "Sorting imports with Ruff..."
$(PYTHON) -m ruff check --fix code/ tests/
@echo "Formatting complete."

format-check: ## Check formatting without applying changes
@echo "Checking Black formatting..."
$(PYTHON) -m black --check code/ tests/
@echo "Checking Ruff import sorting..."
$(PYTHON) -m ruff check --select I --fix code/ tests/
@echo "Format check complete."

test: ## Run tests with pytest
$(PYTHON) -m pytest tests/ -v --tb=short

clean: ## Remove temporary files and caches
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
find . -type f -name "*.pyo" -delete
find . -type d -name ".pytest_cache" -exec rm -r {} +
find . -type d -name "htmlcov" -exec rm -r {} +
find . -type d -name ".ruff_cache" -exec rm -r {} +
rm -rf .coverage
@echo "Cleaned temporary files."
