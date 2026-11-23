.PHONY: install lint format test clean

install:
    pip install -r requirements.txt
    pip install -e .

lint:
    @echo "Running linter..."
    ./scripts/lint.sh

format:
    @echo "Running formatter..."
    ./scripts/format.sh

test:
    @echo "Running tests..."
    pytest tests/ -v

clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    rm -rf .pytest_cache
    rm -rf .ruff_cache
    rm -rf htmlcov
    rm -rf .coverage
    rm -rf coverage.xml
    rm -rf *.egg-info
    rm -rf build
    rm -rf dist
    rm -rf *.egg

# Check formatting without modifying
check-format:
    black --check code/ tests/
    ruff check code/ tests/
