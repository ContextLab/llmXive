.PHONY: lint format check-type test clean

# Lint the codebase using ruff
lint:
	ruff check code/ tests/

# Format the codebase using black and ruff
format:
	ruff check --fix code/ tests/
	black code/ tests/

# Run all tests
test:
	pytest tests/ -v --cov=code

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/

# Install dependencies
install:
	pip install -r requirements.txt
	pip install ruff black pytest pytest-cov
