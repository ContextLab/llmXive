.PHONY: lint format test clean

lint:
    ruff check code/

format:
    black code/ tests/

test:
    python -m pytest tests/ -v

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
