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
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

help:
	@echo "Available targets:"
	@echo "  lint       - Run flake8 and isort checks"
	@echo "  format     - Format code with black and isort"
	@echo "  test       - Run pytest"
	@echo "  clean      - Remove cache files"
	@echo "  install-dev- Install development dependencies and pre-commit hooks"
	@echo "  help       - Show this help message"