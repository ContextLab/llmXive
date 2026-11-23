.PHONY: lint format test clean

# Linting
lint:
	ruff check code/ tests/

# Formatting
format:
	black code/ tests/
	ruff check code/ tests/ --fix

# Run tests
test:
	pytest tests/ -v --cov=code --cov-report=term-missing

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage