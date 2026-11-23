.PHONY: setup lint test clean run-all

setup:
	python -m venv venv
	source venv/bin/activate && pip install -r requirements.txt

lint:
	ruff check code/
	black --check code/

format:
	black code/
	ruff check --fix code/

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache

run-all:
	python code/main.py --stage download
	python code/main.py --stage salience
	python code/main.py --stage fit
	python code/main.py --stage compare