.PHONY: setup lint format test clean data

# Install dependencies
setup:
    pip install -r requirements.txt

# Run linting
lint:
    ruff check .

# Fix linting issues
lint-fix:
    ruff check --fix .

# Check formatting
format-check:
    black --check .

# Format code
format:
    black .

# Run tests
test:
    pytest tests/ -v

# Clean generated files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    rm -rf .pytest_cache/
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf data/raw/*
    rm -rf data/cleaned/*
    rm -rf data/derived/*
    rm -rf data/results/*
    rm -rf figures/*
    rm -rf reports/*

# Initialize data directories
data:
    mkdir -p data/raw data/cleaned data/derived data/results
    touch data/checksums.txt

# Full setup
all: setup lint format test