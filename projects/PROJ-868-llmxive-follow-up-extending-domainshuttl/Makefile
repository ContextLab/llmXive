# Makefile for llmXive project development tools

.PHONY: lint format check type test clean

# Run linter (ruff)
lint:
	ruff check src/ tests/

# Run formatter (black)
format:
	black src/ tests/
	ruff check --fix src/ tests/

# Check code quality without fixing
check:
	ruff check src/ tests/
	black --check src/ tests/

# Run type checking (optional, requires mypy)
type:
	mypy src/

# Run tests (placeholder for future)
test:
	pytest tests/ -v

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/