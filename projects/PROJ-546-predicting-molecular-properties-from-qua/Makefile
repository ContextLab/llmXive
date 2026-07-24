.PHONY: all setup lint test clean data descriptors train

PYTHON := python3
PIP := pip3

all: setup lint test

setup:
	$(PIP) install -r code/requirements.txt
	$(PIP) install ruff black

lint:
	ruff check code/
	black --check code/

format:
	black code/

test:
	$(PYTHON) -m pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf data/processed/*
	rm -rf data/cache/*

data:
	$(PYTHON) code/download_data.py

descriptors:
	$(PYTHON) code/generate_descriptors.py

train:
	$(PYTHON) code/train_models.py
