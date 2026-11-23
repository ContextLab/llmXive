# Makefile for PROJ-362: Linting, Formatting, and Testing
# Prerequisites: Ensure virtual environment is activated and dependencies installed

.PHONY: help lint format format-check test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

lint: ## Run ruff linter (check only, no auto-fix)
	ruff check code/ tests/

lint-fix: ## Run ruff linter with auto-fix
	ruff check --fix code/ tests/

format: ## Run black formatter
	black code/ tests/

format-check: ## Check formatting with black (no changes)
	black --check code/ tests/

check: ## Run all checks (lint + format)
	$(MAKE) lint
	$(MAKE) format-check

fix: ## Run all auto-fixes
	$(MAKE) lint-fix
	$(MAKE) format

test: ## Run pytest
	pytest

clean: ## Clean up temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -f .coverage
	rm -rf htmlcov/

install-hooks: ## Install pre-commit hooks
	pre-commit install

run-hooks: ## Run pre-commit hooks on all files
	pre-commit run --all-files
