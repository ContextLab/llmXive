.PHONY: format lint check test clean

# Configuration
PYTHON = python
CODE_DIR = code

format:
	@echo "Formatting code with Black..."
	black $(CODE_DIR)
	@echo "Sorting imports with Ruff..."
	ruff check --fix $(CODE_DIR)

lint:
	@echo "Running linter (Ruff)..."
	ruff check $(CODE_DIR)
	@echo "Checking formatting (Black)..."
	black --check $(CODE_DIR)

check: lint
	@echo "All checks passed!"

test:
	@echo "Running tests..."
	pytest

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov
	rm -rf build dist *.egg-info
