.PHONY: lint format test clean help

help:
	@echo "Available targets:"
	@echo "  lint      - Run flake8 linting checks"
	@echo "  format    - Format code with black and isort"
	@echo "  test      - Run pytest"
	@echo "  clean     - Remove build artifacts and cache"

lint:
	@echo "Running flake8..."
	flake8 code/ tests/ --count --statistics
	@echo "Linting complete."

format:
	@echo "Running isort..."
	isort code/ tests/
	@echo "Running black..."
	black code/ tests/
	@echo "Formatting complete."

test:
	@echo "Running pytest..."
	pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.mypy_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name 'build' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name 'dist' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true