.PHONY: lint format check test clean

lint:
	ruff check .

format:
	black .
	ruff check --fix .

check:
	ruff check .
	black --check .

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf .ruff_cache
	rm -rf .pytest_cache
	rm -rf build dist