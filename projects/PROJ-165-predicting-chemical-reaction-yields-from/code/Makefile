.PHONY: lint format check

# Run linters
lint:
	ruff check code/
	flake8 code/

# Run formatter
format:
	black code/
	ruff check --fix code/

# Check formatting without modifying
check:
	black --check code/
	ruff check code/

# Install dev dependencies
install-dev:
	pip install -r requirements.txt
	pip install ruff black flake8
