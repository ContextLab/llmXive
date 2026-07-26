.PHONY: setup clean test lint format

setup:
	python code/setup_directories.py

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

test:
	pytest

lint:
	ruff check code/ tests/

format:
	black code/ tests/

all: setup lint format test
