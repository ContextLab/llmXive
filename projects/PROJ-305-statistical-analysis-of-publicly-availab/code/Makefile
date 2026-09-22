# Makefile for development tasks
.PHONY: format lint test clean

format:
	black code/
	ruff check --fix code/

lint:
	ruff check code/
	flake8 code/
	mypy code/

test:
	pytest code/tests/

clean:
	find code/ -type d -name "__pycache__" -exec rm -r {} +
	find code/ -type f -name "*.pyc" -delete
	find code/ -type f -name "*.pyo" -delete
	rm -rf code/.pytest_cache code/.mypy_cache
