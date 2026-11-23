# Makefile for linting, formatting, and testing
# Usage:
#   make lint       -> Run Ruff linter
#   make format     -> Run Black formatter
#   make check      -> Run both lint and format checks
#   make test       -> Run pytest
#   make clean      -> Clean build artifacts

.PHONY: lint format check test clean

# Run Ruff linter
lint:
	ruff check code/ tests/

# Run Black formatter (dry run to check formatting)
format-check:
	black --check code/ tests/

# Run Black formatter (fix files)
format:
	black code/ tests/

# Run both lint and format checks
check: lint format-check
	@echo "All checks passed."

# Run tests
test:
	pytest tests/ -v

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info/ htmlcov/ .coverage
	@echo "Cleaned build artifacts."
