.PHONY: lint format test clean

# Lint the codebase
lint:
	@echo "Running linters..."
	@bash scripts/lint.sh

# Format the codebase
format:
	@echo "Running formatters..."
	@bash scripts/format.sh

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v

# Clean up generated files
clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name htmlcov -exec rm -rf {} +
	rm -rf .coverage

# Default target
all: lint format test
