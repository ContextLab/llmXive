# Makefile for PROJ-220
# Provides shortcuts for linting, formatting, and testing

.PHONY: lint format check-format test clean

# Run linter (Ruff)
lint:
	ruff check code/ tests/

# Auto-fix linting issues where possible
lint-fix:
	ruff check --fix code/ tests/

# Format code with Black
format:
	black code/ tests/

# Check formatting without modifying files
check-format:
	black --check code/ tests/

# Run tests
test:
	pytest tests/ -v

# Clean generated artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf .ruff_cache/
