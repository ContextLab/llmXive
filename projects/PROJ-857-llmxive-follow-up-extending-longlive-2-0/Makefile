.PHONY: lint format check

lint:
	flake8 code/ tests/
	isort --check-only code/ tests/

format:
	black code/ tests/
	isort code/ tests/

check: lint

install-dev:
	pip install -e ".[dev]"

setup-hooks:
	pre-commit install
