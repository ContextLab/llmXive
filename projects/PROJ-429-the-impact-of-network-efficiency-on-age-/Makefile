.PHONY: lint format test clean check-all

# Formatting with Black
format:
	@echo "Running Black formatter..."
	black code/ tests/

# Linting with Ruff
lint:
	@echo "Running Ruff linter..."
	ruff check code/ tests/

# Type checking (optional, requires mypy)
type-check:
	@echo "Running MyPy type checker..."
	mypy code/ --ignore-missing-imports

# Run all quality checks
check-all: lint format

# Clean generated files
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf htmlcov/ .coverage

# Run tests (requires pytest, added to requirements if needed)
test:
	@echo "Running tests..."
	python -m pytest tests/ -v --tb=short