.PHONY: lint format check lint-fix test help

# Default target
help:
	@echo "Available targets:"
	@echo "  make lint       - Run flake8 linting"
	@echo "  make format     - Format code with black and isort"
	@echo "  make lint-fix   - Auto-fix linting issues where possible"
	@echo "  make test       - Run pytest"
	@echo "  make check      - Run lint and tests"

# Linting
lint:
	@echo "Running flake8..."
	flake8 code/

# Formatting
format:
	@echo "Formatting with black and isort..."
	black code/
	isort code/

# Lint fix (black handles most, flake8 does not auto-fix all)
lint-fix:
	@echo "Running black and isort to fix formatting..."
	black code/
	isort code/
	@echo "Re-running flake8 to check remaining issues..."
	flake8 code/ || true

# Tests
test:
	@echo "Running pytest..."
	pytest code/tests/ -v

# Full check
check: lint test
	@echo "All checks passed!"
