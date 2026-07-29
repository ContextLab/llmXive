.PHONY: install lint format test clean

install:
    pip install -e ".[dev]"

lint:
    ruff check code/ tests/

format:
    black code/ tests/
    ruff check --fix code/ tests/

test:
    pytest tests/ -v --cov=code --cov-report=term-missing

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    rm -rf .coverage coverage.xml htmlcov/ .pytest_cache/

pre-commit:
    pre-commit run --all-files