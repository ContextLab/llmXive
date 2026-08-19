.PHONY: lint format test clean

lint:
	flake8 code/ tests/

format:
	black code/ tests/

format-check:
	black --check code/ tests/

test:
	pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .coverage htmlcov
