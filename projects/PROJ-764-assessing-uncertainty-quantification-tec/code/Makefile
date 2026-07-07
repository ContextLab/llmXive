.PHONY: lint format check format-check clean

# Linting with Ruff
lint:
	ruff check code/

# Fix linting issues automatically
lint-fix:
	ruff check --fix code/

# Formatting with Black
format:
	black code/

# Check formatting without applying changes
format-check:
	black --check code/

# Run all checks
check: format-check lint

# Run all formatters
fix: format lint-fix

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf build
	rm -rf dist
	rm -rf results/
	rm -rf data/processed/*
	rm -rf data/raw/*
	rm -rf logs/