.PHONY: lint format test clean install

install:
	pip install -r requirements.txt

lint:
	ruff check code/ tests/

format:
	black code/ tests/
	ruff check --fix code/ tests/

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/ .coverage coverage.xml
