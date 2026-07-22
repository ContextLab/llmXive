.PHONY: lint format test clean

lint:
	flake8 code/

format:
	black code/

format-check:
	black --check code/

test:
	pytest code/tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov/
	rm -rf build/ dist/