.PHONY: lint format type-check test clean

lint:
	ruff check code/

format:
	black code/

type-check:
	mypy code/

test:
	pytest tests/ -v --cov=code --cov-report=term-missing

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete

all: format lint type-check test