.PHONY: lint format test clean

lint:
	flake8 code/
	pylint code/ --ignore-patterns="^test_.*\.py$"

format:
	black code/
	isort code/

test:
	pytest tests/ -v --cov=code --cov-report=html

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .coverage htmlcov/
	rm -rf data/processed/* data/results/*
	rm -rf build/ dist/ *.egg-info/
