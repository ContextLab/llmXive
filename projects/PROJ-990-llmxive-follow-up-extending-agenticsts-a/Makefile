.PHONY: lint format test clean

lint:
	ruff check code/ tests/

format:
	ruff format code/ tests/
	black code/ tests/

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete

check: lint format test
	@echo "All checks passed."
