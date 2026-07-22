.PHONY: install lint format test clean

install:
    pip install -r requirements.txt

lint:
    ruff check code/src code/tests
    black --check code/src code/tests

format:
    ruff check --fix code/src code/tests
    black code/src code/tests
    isort code/src code/tests

test:
    pytest code/tests -v --tb=short

clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type d -name "*.egg-info" -exec rm -r {} +
    rm -rf .coverage coverage.xml htmlcov/ .pytest_cache/

all: install lint format test