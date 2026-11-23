.PHONY: install lint format test clean

install:
	pip install -r requirements.txt

lint:
	ruff check code/ tests/

format:
	black code/ tests/
	ruff check --fix code/ tests/

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf .coverage htmlcov/ .pytest_cache/