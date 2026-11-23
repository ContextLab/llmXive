.PHONY: lint format test clean install-dev

# Install development dependencies
install-dev:
    pip install -e ".[dev]"

# Run linter (flake8)
lint:
    flake8 code/ tests/

# Run formatter (black) - check only
format-check:
    black --check code/ tests/

# Run formatter (black) - fix files
format:
    black code/ tests/
    isort code/ tests/

# Run tests
test:
    pytest tests/ -v

# Run all quality checks
quality: lint format-check test

# Clean generated files
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type d -name "*.egg-info" -exec rm -rf {} +
    rm -rf .mypy_cache
    rm -rf .pytest_cache
    rm -rf build dist
    rm -rf data/processed/*.csv data/processed/*.json data/processed/*.png 2>/dev/null || true
    rm -rf data/raw/* 2>/dev/null || true
    rm -f data/checksums.txt 2>/dev/null || true
