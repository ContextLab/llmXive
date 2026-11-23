.PHONY: lint format test clean

lint:
	ruff check code/

format:
	black code/
	ruff check --fix code/

test:
	pytest code/tests/ -v

clean:
	find code/ -type d -name "__pycache__" -exec rm -rf {} +
	find code/ -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/ htmlcov/ .coverage

init:
	pip install -r requirements.txt
	mkdir -p data/raw data/processed data/results figures tests/unit tests/integration tests/contract
	touch data/raw/.gitkeep data/processed/.gitkeep data/results/.gitkeep figures/.gitkeep