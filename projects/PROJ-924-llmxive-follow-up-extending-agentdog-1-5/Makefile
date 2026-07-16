.PHONY: format lint check test install-dev

install-dev:
    pip install -e ".[dev]"
    pre-commit install

format:
    black code/ tests/
    ruff format code/ tests/

lint:
    ruff check code/ tests/
    black --check code/ tests/

check: lint

test:
    pytest tests/ -v

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type d -name ".pytest_cache" -exec rm -rf {} +
    rm -rf .mypy_cache
    rm -rf build dist *.egg-info