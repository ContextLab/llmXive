.PHONY: lint format test clean

format:
	black code/ tests/

lint:
	flake8 code/ tests/
	black --check code/ tests/

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache