.PHONY: lint format check format-check test clean

# Linting and Formatting targets
lint:
	ruff check code/ tests/

format:
	black code/ tests/
	ruff check --fix code/ tests/

format-check:
	black --check code/ tests/
	ruff check code/ tests/

test:
	pytest tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .mypy_cache/
	rm -rf .tox/
	rm -rf .venv/
	rm -rf venv/
	rm -rf .eggs/
	rm -rf *.egg
	rm -rf .hypothesis/
	rm -rf .cache/
	rm -rf .mypy_cache/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .tox/
	rm -rf .venv/
	rm -rf venv/
	rm -rf .eggs/
	rm -rf *.egg
	rm -rf .hypothesis/
	rm -rf .cache/