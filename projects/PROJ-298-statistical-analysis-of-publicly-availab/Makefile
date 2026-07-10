.PHONY: lint format format-check test clean

lint:
	flake8 code/ tests/

format:
	isort code/ tests/
	black code/ tests/

format-check:
	isort --check code/ tests/
	black --check code/ tests/

test:
	python -m pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf build dist .eggs *.egg-info
	rm -rf .coverage coverage.xml htmlcov/
	rm -rf .pytest_cache .mypy_cache .tox/