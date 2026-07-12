.PHONY: lint format test clean

lint:
	@echo "Running linters..."
	@./scripts/lint.sh

format:
	@echo "Running formatters..."
	@./scripts/format.sh

test:
	@echo "Running tests..."
	pytest code/tests/

clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
