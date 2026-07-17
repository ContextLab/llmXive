.PHONY: setup clean lint format test

setup:
	python -m venv venv
	source venv/bin/activate && pip install -r requirements.txt

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/

lint:
	ruff check code/ tests/

format:
	black code/ tests/

test:
	pytest tests/ -v

run-ingestion:
	python code/ingestion.py

run-features:
	python code/features.py

run-inference:
	python code/inference.py

run-labeling:
	python code/labeling.py

run-modeling:
	python code/modeling.py

run-full:
	make run-ingestion && make run-features && make run-inference && make run-labeling && make run-modeling