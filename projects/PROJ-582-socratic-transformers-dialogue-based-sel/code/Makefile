.PHONY: lint format test clean

# Run linters (ruff and black check)
lint:
	@echo "Running linters..."
	@bash scripts/lint.sh

# Run formatters (ruff fix and black)
format:
	@echo "Running formatters..."
	@bash scripts/format.sh

# Run tests
test:
	@echo "Running tests..."
	pytest

# Clean build artifacts
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/

# Default target
all: lint test
