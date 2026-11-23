.PHONY: setup lint format test clean

setup:
	pip install -r code/requirements.txt

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
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf data/raw/*
	rm -rf data/processed/*
	rm -rf reports/*
	rm -rf logs/*