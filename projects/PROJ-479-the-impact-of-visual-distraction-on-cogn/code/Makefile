.PHONY: lint format check install

# Install development dependencies
install:
	pip install -r requirements.txt
	pip install black ruff pytest

# Run formatter (Black)
format:
	black code/ tests/

# Run linter (Ruff)
lint:
	ruff check code/ tests/

# Run formatter check (dry run)
format-check:
	black --check code/ tests/

# Run linter check
lint-check:
	ruff check code/ tests/

# Full quality check
check: format-check lint-check

# Default target
all: check