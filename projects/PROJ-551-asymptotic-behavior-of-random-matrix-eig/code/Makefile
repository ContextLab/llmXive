# Makefile for linting and formatting
.PHONY: lint format check

lint:
	@echo "Running ruff lint..."
	ruff check code/ tests/

format:
	@echo "Running black formatter..."
	black code/ tests/
	@echo "Running ruff format (if available) or auto-fix..."
	ruff check --fix code/ tests/

check: lint format
	@echo "Linting and formatting complete."

test:
	@echo "Running pytest..."
	pytest tests/ -v

install-dev:
	@echo "Installing development dependencies..."
	pip install -e ".[dev]"
