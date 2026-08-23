.PHONY: format lint check lint-check

# Format code with black and sort imports with isort (via ruff)
format:
	black code/
	ruff check --fix code/

# Run linter without auto-fix
lint:
	ruff check code/

# Run formatter check (dry run)
check:
	black --check code/

# Run linter check (dry run)
lint-check:
	ruff check code/

# Install development dependencies
dev-install:
	pip install -r requirements.txt
	pip install ruff black
