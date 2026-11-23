.PHONY: lint format check-format test clean

# Linting using Ruff
lint:
	ruff check .

# Formatting using Black
format:
	black .

# Check formatting without modifying files
check-format:
	black --check .

# Run all checks
check: lint check-format

# Fix lint issues automatically where possible
fix-lint:
	ruff check --fix .

# Run tests
test:
	pytest

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov coverage.xml .coverage
