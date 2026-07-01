.PHONY: lint format test clean

lint:
    ruff check .

format:
    black .
    ruff check --fix .

test:
    pytest tests/ -v --cov=code --cov-report=term-missing

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    rm -rf .pytest_cache .coverage htmlcov/