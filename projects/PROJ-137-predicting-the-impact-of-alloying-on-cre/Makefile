.PHONY: install lint format test clean

install:
    pip install -e ".[dev]"

lint:
    ruff check .

format:
    black .
    ruff check . --fix

test:
    pytest tests/ -v

clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    rm -rf .pytest_cache .coverage htmlcov .mypy_cache