.PHONY: lint format test clean

lint:
	ruff check code/src code/tests

format:
	ruff format code/src code/tests
	black code/src code/tests

check: lint format
	pytest

install-dev:
	pip install -r requirements.txt
	pip install pre-commit
	pre-commit install

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage