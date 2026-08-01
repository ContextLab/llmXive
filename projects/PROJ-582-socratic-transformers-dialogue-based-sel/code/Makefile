.PHONY: lint format check-lint check-format test clean

# Linting and Formatting
lint:
    ruff check .

format:
    black .
    ruff check . --fix

check-lint:
    ruff check .
    ruff check . --output-format=github

check-format:
    black --check .

# Testing
test:
    pytest tests/ -v

# Clean
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    rm -rf .pytest_cache .coverage htmlcov/ dist/ build/

# Default target
all: check-lint check-format test
