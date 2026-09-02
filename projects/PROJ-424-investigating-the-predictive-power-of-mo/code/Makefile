.PHONY: lint format check format-check

# Run linter (ruff)
lint:
	ruff check code/ tests/

# Auto-fix linting issues
lint-fix:
	ruff check --fix code/ tests/

# Format code (black)
format:
	black code/ tests/

# Check formatting without modifying files
format-check:
	black --check code/ tests/

# Run both checks
check: lint format-check

# Run all fixes
fix: lint-fix format
