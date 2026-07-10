.PHONY: lint format check-format test clean

# Linting
lint:
	flake8 code/

# Formatting
format:
	black code/
	isort code/

# Check formatting (fail if not formatted correctly)
check-format:
	black --check code/
	isort --check code/

# Run tests
test:
	pytest code/tests/ -v

# Run tests with coverage
test-coverage:
	pytest code/tests/ -v --cov=code --cov-report=html --cov-report=term-missing

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

# All checks in one command
check: check-format lint

# Default target
all: check test