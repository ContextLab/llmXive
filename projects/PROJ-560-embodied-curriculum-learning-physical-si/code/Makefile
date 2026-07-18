# Makefile for PROJ-560 code quality and formatting

.PHONY: lint format check-format clean

# Run the linter (ruff)
lint:
	ruff check code/src code/tests

# Run the formatter (black) and fix issues automatically
format:
	black code/src code/tests
	ruff check --fix code/src code/tests

# Check formatting without fixing (for CI)
check-format:
	black --check code/src code/tests
	ruff check code/src code/tests

# Install pre-commit hooks
install-hooks:
	pre-commit install

# Run all checks
check: lint check-format

clean:
	find code/ -type d -name __pycache__ -exec rm -rf {} +
	find code/ -type f -name "*.pyc" -delete
	find code/ -type d -name "*.egg-info" -exec rm -rf {} +