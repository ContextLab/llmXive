.PHONY: lint format check install-dev clean

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Run linter (ruff)
lint:
	ruff check .

# Fix lint issues automatically
lint-fix:
	ruff check --fix .

# Format code (black)
format:
	black .

# Run both lint and format
check: lint format

# Clean python cache
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name "PDB" -delete
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage

# Run tests
test:
	pytest tests/ -v --cov=code --cov-report=xml
