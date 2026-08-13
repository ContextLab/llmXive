.PHONY: lint format test clean

lint:
    @echo "Running flake8..."
    flake8 code/
    @echo "Linting complete."

format:
    @echo "Running black..."
    black code/
    @echo "Formatting complete."

check: lint format
    @echo "All checks passed."

test:
    @echo "Running pytest..."
    pytest tests/
    @echo "Tests complete."

clean:
    @echo "Cleaning up..."
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name ".coverage" -delete
    rm -rf .pytest_cache
    @echo "Clean complete."
