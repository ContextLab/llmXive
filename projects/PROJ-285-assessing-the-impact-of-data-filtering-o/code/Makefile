.PHONY: lint format check test

# Linting
lint:
	@echo "Running flake8..."
	flake8 src/ tests/

# Formatting
format:
	@echo "Running black..."
	black src/ tests/
	@echo "Running isort..."
	isort src/ tests/

# Check formatting (dry run)
check-format:
	@echo "Checking black formatting (diff mode)..."
	black --check src/ tests/
	@echo "Checking isort..."
	isort --check-only src/ tests/

# Run tests
test:
	@echo "Running pytest..."
	pytest

# All checks
ci: lint check-format test
	@echo "All checks passed."