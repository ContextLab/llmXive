.PHONY: lint format test clean install-dev

# Python environment management
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Linting and formatting
lint:
	flake8 code/ utils/ tests/

format:
	black code/ utils/ tests/
	isort code/ utils/ tests/

format-check:
	black --check code/ utils/ tests/
	isort --check code/ utils/ tests/

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=code --cov=utils --cov-report=html --cov-report=term-missing

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ htmlcov/ .coverage
	rm -rf results/pipeline.log results/checkpoints/*

# Full quality check
quality: format lint test
	@echo "All quality checks passed!"
