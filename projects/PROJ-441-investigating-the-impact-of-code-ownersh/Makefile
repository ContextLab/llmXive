.PHONY: format lint check clean test

# Formatting using Black
format:
	black code/ tests/

# Linting using Ruff
lint:
	ruff check code/ tests/

# Check formatting (does not modify files)
check-format:
	black --check code/ tests/

# Combined check
check: check-format lint
	@echo "All checks passed."

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf .coverage coverage.xml htmlcov/

# Run tests
test:
	pytest

# Install dependencies
install:
	pip install -e ".[dev]"
