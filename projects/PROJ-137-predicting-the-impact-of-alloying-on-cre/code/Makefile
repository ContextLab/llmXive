.PHONY: lint format test clean install

install:
	pip install -e ".[dev]"

lint:
	ruff check code/

format:
	black code/
	ruff check --fix code/

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf logs/*.log