.PHONY: install lint format test clean

install:
    pip install -r requirements.txt

lint:
    ruff check code/

format:
    black code/

test:
    pytest code/tests/ -v

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
