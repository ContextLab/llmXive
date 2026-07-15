.PHONY: lint format test clean install-dev

install-dev:
	pip install -e ".[dev]"

lint:
	ruff check code/src code/tests

format:
	black code/src code/tests
	ruff check --fix code/src code/tests

test:
	pytest code/tests --cov=src --cov-report=term-missing --cov-report=xml --timeout=300

clean:
	find code -type d -name "__pycache__" -exec rm -rf {} +
	find code -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage coverage.xml

all: lint format test