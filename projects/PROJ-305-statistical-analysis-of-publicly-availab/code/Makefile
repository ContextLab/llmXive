.PHONY: lint format test clean

lint:
	ruff check code/src code/tests
	ruff check --diff code/src code/tests

format:
	black code/src code/tests
	ruff check --fix code/src code/tests

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf .mypy_cache

setup:
	pip install -e ".[dev]"