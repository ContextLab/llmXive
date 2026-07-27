.PHONY: lint format check-lint check-format test clean

# Linting and Formatting
lint:
	ruff check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/ tests/

check-lint:
	ruff check src/ tests/
	@echo "Ruff check passed."

check-format:
	black --check src/ tests/
	@echo "Black check passed."

# Testing
test:
	pytest tests/ -v

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ dist/ build/ *.egg-info/
