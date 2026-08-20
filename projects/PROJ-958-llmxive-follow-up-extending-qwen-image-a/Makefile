.PHONY: format lint test clean

# Format code with Black
format:
	black code/ src/ tests/

# Lint code with Ruff
lint:
	ruff check code/ src/ tests/
	ruff format --check code/ src/ tests/

# Run tests (placeholder for T009/T010 implementation later)
test:
	python -m pytest tests/ -v

# Clean generated artifacts
clean:
	rm -rf .pytest_cache .mypy_cache __pycache__ data/derived/*.csv data/derived/*.json data/derived/images
