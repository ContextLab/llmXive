.PHONY: lint format test clean

lint:
    ruff check code/ tests/

format:
    black code/ tests/
    ruff check --fix code/ tests/

check-format:
    black --check code/ tests/

test:
    pytest tests/ -v --cov=code --cov-report=term-missing

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name ".coverage" -delete
    rm -rf htmlcov/
