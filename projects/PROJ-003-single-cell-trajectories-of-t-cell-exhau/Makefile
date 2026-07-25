.PHONY: lint format check-format test clean

# Lint code using ruff
lint:
	ruff check code/ tests/

# Format code using black
format:
	black code/ tests/

# Check formatting without modifying files
check-format:
	black --check code/ tests/

# Run all tests
test:
	pytest tests/

# Clean up generated files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .ruff_cache htmlcov/ .coverage
