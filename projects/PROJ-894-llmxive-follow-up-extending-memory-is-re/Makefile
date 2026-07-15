.PHONY: lint format test clean

# Lint with Ruff
lint:
	ruff check code/ tests/

# Format with Black
format:
	black code/ tests/

# Check formatting (without modifying)
format-check:
	black --check code/ tests/

# Run tests
test:
	pytest tests/ -v

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache htmlcov/ coverage.xml

# Install dependencies
install:
	pip install -e ".[dev]"

# Full CI check
ci: lint format-check test