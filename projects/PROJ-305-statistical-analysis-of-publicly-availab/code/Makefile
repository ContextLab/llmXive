.PHONY: lint format check format-check

format:
	black code/
	ruff check --fix code/

lint:
	ruff check code/

format-check:
	black --check code/

check: lint format-check

test:
	pytest code/tests/ -v --cov=code/src --cov-report=term-missing

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf code/output/* code/data/processed/*
