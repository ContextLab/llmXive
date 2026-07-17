.PHONY: lint format test clean install

# Install dependencies
install:
	pip install -r requirements.txt
	pip install ruff black pytest

# Run linter (ruff)
lint:
	ruff check code/ tests/

# Run formatter (black)
format:
	black code/ tests/
	ruff check --fix code/ tests/

# Run tests
test:
	pytest tests/ -v

# Clean generated files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage*" -delete
	rm -rf htmlcov/ .pytest_cache/ .tox/
	rm -rf data/processed/*.csv
	rm -rf figures/*.png

# Full clean and reinstall
fresh: clean install
