.PHONY: lint format check-format test clean

# Lint the codebase
lint:
	flake8 code/ tests/

# Format code with Black and sort imports with isort
format:
	isort code/ tests/
	black code/ tests/

# Check formatting (fails if code is not formatted)
check-format:
	isort --check-only code/ tests/
	black --check code/ tests/

# Run tests
test:
	pytest

# Clean up generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	rm -rf data/processed/*.csv data/processed/*.json data/processed/*.md figures/ 2>/dev/null || true

# Full CI check
ci: check-format lint test
