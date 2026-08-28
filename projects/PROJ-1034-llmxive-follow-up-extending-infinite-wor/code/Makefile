# Makefile for development tasks
# Requires: pip install -e ".[dev]" and pre-commit install

.PHONY: install-dev lint format test clean

install-dev:
    pip install -e ".[dev]"

format:
    black code/
    ruff check --fix code/

lint:
    ruff check code/
    black --check code/

test:
    pytest code/tests/

pre-commit-setup:
    pre-commit install

clean:
    find code/ -type d -name "__pycache__" -exec rm -r {} +
    find code/ -type f -name "*.pyc" -delete
    rm -rf .pytest_cache .mypy_cache dist build *.egg-info
