.PHONY: lint format test clean

lint:
	flake8 code/

format:
	black code/
	isort code/

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf .pytest_cache htmlcov .coverage

check: lint test