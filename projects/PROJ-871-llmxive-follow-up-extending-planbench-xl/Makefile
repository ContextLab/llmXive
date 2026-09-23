.PHONY: lint format test clean

lint:
	flake8 code/ tests/
	isort --check-only code/ tests/

format:
	black code/ tests/
	isort code/ tests/

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

install-dev:
	pip install -e ".[dev]"
	pre-commit install

update-hooks:
	pre-commit autoupdate
	pre-commit install
