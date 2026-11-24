.PHONY: format lint test

# Run Black formatter
format:
	@echo "Running Black formatter..."
	python -m black code

# Run Ruff linter
lint:
	@echo "Running Ruff linter..."
	python -m ruff check code

# Run tests (existing test suite)
test:
	pytest -v
