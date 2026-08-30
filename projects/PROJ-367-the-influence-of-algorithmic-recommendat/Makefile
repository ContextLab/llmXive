# Makefile for PROJ-367 Linting and Formatting
# Usage: make lint, make format, make check-all

PYTHON := python3
LINT_CMD := ruff check code/ tests/
FORMAT_CMD := black code/ tests/
ISORT_CMD := isort code/ tests/
ISORT_CHECK_CMD := isort --check code/ tests/

.PHONY: lint format format-check check-all clean

lint:
	@echo "Running Ruff linter..."
	$(LINT_CMD)

format:
	@echo "Running Black formatter..."
	$(FORMAT_CMD)
	@echo "Running Isort..."
	$(ISORT_CMD)

format-check:
	@echo "Checking Black formatting..."
	black --check code/ tests/
	@echo "Checking Isort..."
	$(ISORT_CHECK_CMD)

check-all:
	@echo "Running all checks (Lint + Format)..."
	$(LINT_CMD)
	black --check code/ tests/
	$(ISORT_CHECK_CMD)

clean:
	@echo "Cleaning up temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +