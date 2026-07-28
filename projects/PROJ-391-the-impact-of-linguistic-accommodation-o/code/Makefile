# Makefile for linting and formatting tasks
# Usage:
#   make format       -> Run black to format code
#   make lint         -> Run ruff to check for linting errors
#   make check        -> Run both lint and format checks (dry run)
#   make fix          -> Run lint and format to fix issues automatically

.PHONY: format lint check fix clean

format:
	black code/ tests/

lint:
	ruff check code/ tests/

check:
	black --check code/ tests/
	ruff check code/ tests/

fix:
	black code/ tests/
	ruff check --fix code/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +