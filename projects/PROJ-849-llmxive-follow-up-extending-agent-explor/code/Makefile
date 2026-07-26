.PHONY: lint format check lint-fix check-type test clean

# Configuration
PYTHON := python3
VENV := .venv

# Linting and Formatting
lint:
	ruff check code/

format:
	black code/

lint-fix:
	ruff check --fix code/

# Type checking (optional, requires mypy)
check-type:
	@echo "Type checking skipped for this task (mypy not in requirements yet)"

# Testing
test:
	$(PYTHON) -m pytest tests/ -v

# Cleanup
clean:
	find code/ -type d -name "__pycache__" -exec rm -rf {} +
	find code/ -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Install dependencies
install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

# Default target
all: install lint format test
