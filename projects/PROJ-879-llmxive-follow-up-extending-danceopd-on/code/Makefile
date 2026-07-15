.PHONY: format lint test clean

# Format code with Black
format:
	black code/

# Lint code with Ruff
lint:
	ruff check code/

# Fix lint issues automatically
lint-fix:
	ruff check --fix code/

# Run tests
test:
	pytest tests/ -v

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache
