.PHONY: lint format check format-check test clean

# Linting and Formatting targets
lint:
	ruff check code/
	flake8 code/

format:
	black code/
	ruff check --fix code/

format-check:
	black --check code/
	ruff check code/

test:
	pytest tests/ -v --cov=code --cov-report=term-missing

clean:
	find code/ -type d -name "__pycache__" -exec rm -r {} +
	find code/ -type f -name "*.pyc" -delete
	find code/ -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .coverage htmlcov/
