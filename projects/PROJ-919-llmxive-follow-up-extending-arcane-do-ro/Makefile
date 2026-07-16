.PHONY: lint format check install-dev clean

install-dev:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/

format:
	black src/ tests/

check:
	ruff check src/ tests/
	black --check src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov/ .mypy_cache/