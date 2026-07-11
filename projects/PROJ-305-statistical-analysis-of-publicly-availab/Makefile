.PHONY: format lint test clean

format:
	@echo "Formatting code..."
	@black .
	@ruff check . --fix
	@echo "Done."

lint:
	@echo "Linting code..."
	@ruff check .
	@black --check .
	@echo "Done."

test:
	@echo "Running tests..."
	@pytest
	@echo "Done."

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@rm -rf .pytest_cache .coverage htmlcov
	@echo "Cleaned."
