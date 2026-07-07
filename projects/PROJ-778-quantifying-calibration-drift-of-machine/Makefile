.PHONY: lint format test clean

lint:
    ruff check .

format:
    black .
    ruff check --fix .

test:
    pytest tests/ -v --cov=code --cov-report=term-missing

clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name ".coverage" -delete
    rm -rf htmlcov/
    rm -rf .pytest_cache/
