.PHONY: lint format test clean

lint:
	ruff check code/ tests/

format:
	black code/ tests/
	ruff check --fix code/ tests/

test:
	python -m pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*~" -delete
	rm -rf .pytest_cache .coverage htmlcov/
