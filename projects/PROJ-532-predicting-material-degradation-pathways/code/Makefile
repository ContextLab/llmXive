.PHONY: lint format check install-deps

# Install linting and formatting dependencies
install-deps:
	pip install -r requirements.txt
	pip install ruff black

# Run linter (ruff)
lint:
	ruff check code/

# Auto-fix linting issues where possible
lint-fix:
	ruff check --fix code/

# Format code with Black
format:
	black code/

# Check formatting without modifying files
format-check:
	black --check code/

# Run both lint and format checks
check: lint format-check
