.PHONY: install format lint test clean

# Install dependencies
install:
	pip install -r requirements.txt

# Format code with black
format:
	black code/ tests/

# Lint code with ruff
lint:
	ruff check code/ tests/
	ruff format --check code/ tests/

# Run tests
test:
	pytest tests/

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache .mypy_cache htmlcov/
