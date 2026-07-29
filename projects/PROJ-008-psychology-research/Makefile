.PHONY: setup lint format test clean

setup:
    @echo "Setting up Python environment..."
    python -m venv .venv
    . .venv/bin/activate && pip install --upgrade pip
    . .venv/bin/activate && pip install -r requirements.txt

lint:
    @echo "Running linter..."
    ruff check code/ tests/

format:
    @echo "Running formatter..."
    black code/ tests/

test:
    @echo "Running tests..."
    pytest tests/ -v

clean:
    @echo "Cleaning up..."
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type f -name "Pipfile.lock" -delete
    rm -rf .pytest_cache/
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf coverage.xml
