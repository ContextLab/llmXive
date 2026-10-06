.PHONY: lint format test clean

# Lint the codebase using ruff
lint:
	cd code && ruff check .

# Format the codebase using black
format:
	cd code && black .

# Run unit tests
test:
	cd code && pytest tests/unit -v

# Run all tests (unit + integration)
test-all:
	cd code && pytest tests/ -v

# Clean up generated files
clean:
	rm -rf code/__pycache__
	rm -rf code/tests/__pycache__
	rm -rf .pytest_cache
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

# Check formatting and linting status (fail if not clean)
check:
	cd code && black --check . && ruff check .

# Install dependencies
install:
	pip install -r requirements.txt
