.PHONY: lint format check

# Lint the codebase using ruff
lint:
	ruff check code/ tests/

# Format the codebase using ruff (black-compatible)
format:
	ruff format code/ tests/

# Check formatting without applying changes
format-check:
	ruff format --check code/ tests/

# Run both lint and format check
check: lint format-check

# Install development tools (ruff, black)
install-dev:
	pip install ruff black
