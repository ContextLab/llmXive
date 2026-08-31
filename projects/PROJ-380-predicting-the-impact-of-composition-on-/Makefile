.PHONY: lint format check test clean

# Configuration
PYTHON := python3
RUFF := ruff
BLACK := black
PYTEST := pytest

# Lint: Check code style without modifying
lint:
	@echo "Running linter (ruff)..."
	$(RUFF) check code/ tests/
	@echo "Lint check complete."

# Format: Automatically fix formatting issues
format:
	@echo "Running formatter (black)..."
	$(BLACK) code/ tests/
	@echo "Running linter fix (ruff)..."
	$(RUFF) check --fix code/ tests/ || true
	@echo "Format complete."

# Check: Run both lint and format checks (fail if dirty)
check: lint
	@echo "Checking code style compliance..."
	$(BLACK) --check code/ tests/
	@echo "All style checks passed."

# Test: Run the test suite
test:
	@echo "Running tests..."
	$(PYTEST)
	@echo "Tests complete."

# Clean: Remove generated artifacts
clean:
	@echo "Cleaning up..."
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "Clean complete."

# Default target
all: check test
	@echo "Pipeline validation complete."
