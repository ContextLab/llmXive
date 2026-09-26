.PHONY: install format lint test clean

PYTHON := python3.11

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"
	$(PYTHON) -m pre-commit install

format:
	@bash scripts/format.sh

lint:
	@bash scripts/lint.sh

test:
	$(PYTHON) -m pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .mypy_cache dist/ build/ *.egg-info/