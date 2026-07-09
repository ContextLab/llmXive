.PHONY: setup lint test clean

setup:
    python -m venv venv
    source venv/bin/activate && pip install -r code/requirements.txt

lint:
    ruff check code/
    black --check code/

format:
    black code/

test:
    pytest tests/ -v

clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    rm -rf .pytest_cache/
    rm -rf htmlcov/
    rm -rf .coverage
