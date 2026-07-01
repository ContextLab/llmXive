.PHONY: lint format test clean install-dev

install-dev:
	pip install -e ".[dev]"

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
	rm -rf .coverage htmlcov/

all: lint format-check test
