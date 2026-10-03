# Makefile for llmXive COVID-19 VAERS Analysis Pipeline
# Provides convenient shortcuts for linting, formatting, and testing

.PHONY: help lint format format-check test clean install-dev

# Default target
help:
	@echo "llmXive COVID-19 VAERS Analysis Pipeline"
	@echo ""
	@echo "Available targets:"
	@echo "  make lint       - Run ruff linter on all Python files"
	@echo "  make format     - Run black formatter on all Python files"
	@echo "  make format-check - Check formatting without modifying files"
	@echo "  make test       - Run pytest with coverage"
	@echo "  make clean      - Remove temporary files and caches"
	@echo "  make install-dev - Install development dependencies"

# Run linter
lint:
	@echo "Running ruff linter..."
	ruff check code/

# Format code
format:
	@echo "Running black formatter..."
	black code/

# Check formatting
format-check:
	@echo "Checking code formatting..."
	black --check code/

# Run tests
test:
	@echo "Running tests with coverage..."
	pytest code/tests/ --cov=code/src --cov-report=term-missing

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf code/__pycache__
	rm -rf code/src/__pycache__
	rm -rf code/tests/__pycache__
	rm -rf code/scripts/__pycache__
	rm -rf code/data/raw/*.zip
	rm -rf code/data/raw/*.csv
	rm -rf code/data/processed/*.parquet
	rm -rf code/data/processed/*.csv
	rm -rf code/output/*
	rm -rf code/logs/*

# Install development dependencies
install-dev:
	@echo "Installing development dependencies..."
	pip install -e ".[dev]"
