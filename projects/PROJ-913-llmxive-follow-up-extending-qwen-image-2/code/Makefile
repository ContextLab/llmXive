.PHONY: lint format check lint-fix clean

# Default target
all: lint format

# Run linter (Ruff)
lint:
	@echo "Running Ruff linter..."
	ruff check code/

# Run formatter (Black)
format:
	@echo "Running Black formatter..."
	black code/

# Fix linting issues automatically (Ruff)
lint-fix:
	@echo "Running Ruff fixer..."
	ruff check --fix code/

# Combined check: format then lint
check: format lint
	@echo "Code style check complete."

# Clean temporary files
clean:
	@echo "Cleaning up..."
	find code/ -type f -name "*.pyc" -delete
	find code/ -type d -name "__pycache__" -delete
	rm -rf .mypy_cache .pytest_cache
