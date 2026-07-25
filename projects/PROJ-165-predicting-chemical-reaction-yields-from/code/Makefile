.PHONY: lint format test clean

lint:
    ruff check code/
    black --check code/

format:
    ruff check --fix code/
    black code/

test:
    pytest code/tests/ -v

clean:
    find code/ -type d -name "__pycache__" -exec rm -rf {} +
    find code/ -type f -name "*.pyc" -delete
    rm -rf .pytest_cache
    rm -rf .ruff_cache
    rm -rf htmlcov
    rm -rf .coverage
    rm -rf coverage.xml