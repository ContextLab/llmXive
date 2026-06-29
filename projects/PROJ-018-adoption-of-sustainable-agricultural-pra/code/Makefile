.PHONY: lint format check

# Lint the codebase using ruff
lint:
	ruff check code/

# Format the codebase using black
format:
	black code/

# Run both lint and format checks
check: lint format

# Install development dependencies
install-dev:
	pip install -e ".[dev]"
