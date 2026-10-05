.PHONY: lint format check test clean

# Lint code using ruff
lint:
	ruff check code/

# Format code using black
format:
	black code/
	ruff check --fix code/

# Check syntax only (fast)
check:
	python -m py_compile code/**/*.py

# Run tests
test:
	pytest

# Clean build artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ .pytest_cache/