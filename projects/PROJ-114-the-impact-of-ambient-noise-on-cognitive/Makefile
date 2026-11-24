.PHONY: help install lint format test clean

help:
	@echo "Available targets:"
	@echo "  install    - Install dependencies"
	@echo "  lint       - Run flake8 linter"
	@echo "  format     - Format code with black and isort"
	@echo "  test       - Run tests with pytest"
	@echo "  clean      - Remove build artifacts and cache"

install:
	pip install -r code/requirements.txt

lint:
	flake8 code/ tests/

format:
	black code/ tests/
	isort code/ tests/

test:
	pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info
