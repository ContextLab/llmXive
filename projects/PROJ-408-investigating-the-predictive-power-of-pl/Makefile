# Makefile for llmXive Phylogeny Project
# Provides convenient commands for linting, formatting, and testing

.PHONY: lint format test clean setup

# Install development dependencies
setup:
	pip install -r requirements.txt -r requirements-dev.txt

# Run linter (ruff) with strict settings
# Enforces unused imports (F401) and missing type hints (ANN)
lint:
	ruff check code/ tests/ scripts/

# Auto-fix linting issues where safe
lint-fix:
	ruff check --fix code/ tests/ scripts/

# Format code with Black
format:
	black code/ tests/ scripts/

# Run all tests
test:
	pytest tests/ -v

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	rm -rf dist/ build/ *.egg-info/

# Run full CI check locally
ci: lint format test
	@echo "CI checks passed."