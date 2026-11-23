.PHONY: lint format check test clean

# Run Ruff to check for linting errors without auto-fixing
lint:
	ruff check code/ tests/

# Run Ruff to automatically fix fixable linting errors
lint-fix:
	ruff check --fix code/ tests/

# Run Black to format code
format:
	black code/ tests/

# Run all checks: linting and formatting (dry run for black)
check:
	ruff check code/ tests/
	black --check code/ tests/

# Run pytest
test:
	pytest tests/ -v

# Clean up generated files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".ruff_cache" -exec rm -r {} +
	rm -rf .coverage coverage.xml htmlcov/

# Install dependencies
install:
	pip install -r code/requirements.txt

# Install dev dependencies (if any were added later)
install-dev: install
	pip install ruff black pytest

# Default target
all: check test