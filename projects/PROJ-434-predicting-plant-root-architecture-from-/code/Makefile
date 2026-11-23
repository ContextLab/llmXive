.PHONY: lint format check test

# Run formatter and fix issues
format:
	black code/
	ruff check --fix code/

# Run linter (read-only)
lint:
	ruff check code/
	black --check code/

# Run all checks (lint + format check)
check: lint

# Run tests
test:
	pytest tests/ -v --cov=code

# Install dev dependencies
install-dev:
	pip install -r requirements-dev.txt
