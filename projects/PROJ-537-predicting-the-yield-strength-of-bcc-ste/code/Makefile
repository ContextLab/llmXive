.PHONY: lint format test clean

# Lint the codebase
lint:
	@echo "Running flake8..."
	flake8 code/ tests/ --config=code/.flake8
	@echo "Lint check complete."

# Format the codebase
format:
	@echo "Running black..."
	black code/ tests/
	@echo "Running isort..."
	isort code/ tests/
	@echo "Format complete."

# Run tests
test:
	@echo "Running pytest..."
	pytest tests/ -v --tb=short
	@echo "Tests complete."

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	@echo "Clean complete."

# Check format (dry run)
check-format:
	@echo "Checking format (black --check)..."
	black --check code/ tests/
	@echo "Checking isort..."
	isort --check code/ tests/
	@echo "Format check complete."
