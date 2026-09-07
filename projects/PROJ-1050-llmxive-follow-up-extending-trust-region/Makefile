.PHONY: install lint format test clean

install:
    pip install -r code/requirements.txt

lint:
    ruff check code/ tests/

format:
    black code/ tests/
    ruff check --fix code/ tests/

test:
    pytest

clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    rm -rf .pytest_cache
    rm -rf .coverage
    rm -rf htmlcov
    rm -rf build
    rm -rf dist
    rm -rf *.egg-info
