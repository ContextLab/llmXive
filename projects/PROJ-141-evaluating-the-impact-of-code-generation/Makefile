.PHONY: lint format test clean

# Linting and formatting targets
lint:
    @echo "Running flake8..."
    flake8 code/ tests/
    @echo "Running black --check..."
    black --check code/ tests/
    @echo "Linting complete."

format:
    @echo "Running black formatter..."
    black code/ tests/
    @echo "Formatting complete."

test:
    @echo "Running pytest..."
    pytest tests/ -v --tb=short
    @echo "Tests complete."

clean:
    @echo "Cleaning up..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
    @echo "Clean complete."

# Install linting dependencies
install-lint:
    @echo "Installing linting tools..."
    pip install black flake8
    @echo "Linting tools installed."

# Run all checks
check: lint test
    @echo "All checks passed."
