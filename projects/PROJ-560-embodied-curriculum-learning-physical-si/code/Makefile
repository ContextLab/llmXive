.PHONY: lint format check test install-dev

# Lint the codebase using Ruff
lint:
	@echo "Running Ruff lint..."
	cd code && ruff check .

# Format the codebase using Black and Ruff
format:
	@echo "Running Black formatter..."
	cd code && black .
	@echo "Running Ruff formatter..."
	cd code && ruff format .

# Check both lint and format
check: lint format
	@echo "All checks passed."

# Run tests
test:
	@echo "Running tests..."
	cd code && pytest tests/ -v

# Install development dependencies
install-dev:
	@echo "Installing development dependencies..."
	pip install -e code/
	pip install ruff black pytest

# Setup environment
setup: install-dev
	@echo "Environment setup complete. Run 'make check' to verify."
