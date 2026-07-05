.PHONY: lint format check format-check clean
  
# Lint the codebase using ruff
lint:
	ruff check code/

# Format the codebase using black
format:
	black code/
	ruff check --fix code/

# Check formatting without applying changes
format-check:
	black --check code/
	ruff check code/

# Clean generated files
clean:
	find code/ -type d -name "__pycache__" -exec rm -rf {} +
	find code/ -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Run all checks (lint and format)
check: format-check lint
	@echo "All checks passed!"

# Run tests
test:
	pytest