# Makefile for llmXive Brain Music Project
# Provides shortcuts for linting, formatting, and testing

.PHONY: help lint format check test clean

PYTHON := python3
VENV := .venv

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

lint: ## Run ruff to check code style and logic
	$(PYTHON) -m ruff check src/ tests/

format: ## Format code with black and sort imports with isort
	$(PYTHON) -m black src/ tests/
	$(PYTHON) -m isort src/ tests/

check: ## Run both lint and format checks (without modifying files)
	$(PYTHON) -m ruff check src/ tests/
	$(PYTHON) -m black --check src/ tests/
	$(PYTHON) -m isort --check src/ tests/

test: ## Run pytest
	$(PYTHON) -m pytest

clean: ## Remove temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .ruff_cache

setup: ## Create virtual environment and install dependencies
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt
	@echo "Setup complete. Activate with: source $(VENV)/bin/activate"