.PHONY: install lint format test clean

install:
    pip install -r requirements.txt

lint:
    ruff check code/ tests/

format:
    black code/ tests/
    ruff check --fix code/ tests/

test:
    pytest tests/

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    rm -rf .pytest_cache
    rm -rf .coverage
    rm -rf htmlcov/

run-baseline:
    python code/main.py --mode baseline

run-cap:
    python code/main.py --mode cap

run-batch:
    python code/main.py --mode batch