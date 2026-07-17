.PHONY: lint format check-style install-dev

install-dev:
	pip install -e ".[dev]"
	pre-commit install

format:
	black code/ tests/ simulation/ evaluation/ analysis/
	isort code/ tests/ simulation/ evaluation/ analysis/

lint:
	flake8 code/ tests/ simulation/ evaluation/ analysis/

check-style:
	black --check code/ tests/ simulation/ evaluation/ analysis/
	isort --check-only code/ tests/ simulation/ evaluation/ analysis/

all: format lint
	@echo "Formatting and linting complete."
