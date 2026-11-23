.PHONY: lint format check install-dev test

install-dev:
	pip install -e ".[dev]"
	pre-commit install

format:
	black src/ tests/
	ruff check --fix src/ tests/

lint:
	ruff check src/ tests/
	black --check src/ tests/

check: lint

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/ .pytest_cache/