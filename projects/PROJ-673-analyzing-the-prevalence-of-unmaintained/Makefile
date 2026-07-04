.PHONY: install lint format test clean

install:
    pip install -e ".[dev]"

lint:
    ruff check .

format:
    black .
    ruff check --fix .

test:
    pytest

clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    rm -rf .pytest_cache
    rm -rf .coverage
    rm -rf htmlcov