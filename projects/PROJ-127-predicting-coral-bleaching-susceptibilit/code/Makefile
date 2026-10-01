.PHONY: lint format check test clean

# Lint the codebase using ruff
lint:
	ruff check code/

# Format the codebase using ruff (black replacement)
format:
	ruff format code/

# Check and fix linting issues automatically
fix:
	ruff check --fix code/
	ruff format code/

# Run unit tests
test:
	pytest tests/unit/ -v

# Clean generated artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .ruff_cache
