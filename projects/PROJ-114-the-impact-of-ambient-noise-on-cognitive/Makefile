.PHONY: setup lint test clean run-power run-synth run-ingest run-analyze help

setup:
	python -m venv venv
	source venv/bin/activate && pip install -r requirements.txt
	pre-commit install

lint:
	flake8 code/ tests/
	black --check code/ tests/

format:
	black code/ tests/

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

run-power:
	python code/scripts/power_analysis.py

run-synth:
	python code/scripts/generate_synthetic_data.py

run-ingest:
	python code/scripts/run_ingestion.py

run-analyze:
	python code/scripts/run_analysis.py

help:
	@echo "Available targets:"
	@echo "  setup       - Create virtual environment and install dependencies"
	@echo "  lint        - Run flake8 and black checks"
	@echo "  format      - Format code with black"
	@echo "  test        - Run pytest"
	@echo "  clean       - Remove cache and temporary files"
	@echo "  run-power   - Run power analysis"
	@echo "  run-synth   - Generate synthetic data"
	@echo "  run-ingest  - Run data ingestion pipeline"
	@echo "  run-analyze - Run statistical analysis"
	@echo "  help        - Show this help message"