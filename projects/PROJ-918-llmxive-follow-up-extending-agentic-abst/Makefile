.PHONY: install lint format check test clean

install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

lint:
	ruff check code/
	flake8 code/

format:
	black code/
	ruff format code/

check: lint format

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
