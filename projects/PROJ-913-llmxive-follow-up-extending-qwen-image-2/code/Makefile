.PHONY: lint format check lint-check

# Lint code using ruff (primary) and flake8 (secondary)
lint:
	@echo "Running Ruff..."
	@ruff check code/
	@echo "Running Flake8..."
	@flake8 code/

# Format code using Black
format:
	@echo "Running Black formatter..."
	@black code/

# Check linting without auto-fixing (for CI)
lint-check:
	@echo "Checking Ruff (no fix)..."
	@ruff check --diff code/ || exit 1
	@echo "Checking Flake8..."
	@flake8 code/

# Check formatting without applying changes (for CI)
format-check:
	@echo "Checking Black formatting..."
	@black --check code/

# Full pre-commit style check
pre-commit: lint-check format-check
	@echo "All checks passed!"
