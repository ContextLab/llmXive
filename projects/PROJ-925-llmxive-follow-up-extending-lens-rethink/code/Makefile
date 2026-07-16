.PHONY: lint format check test help

help:
	@echo "Available commands:"
	@echo "  make lint   - Run linter (ruff)"
	@echo "  make format - Format code (black + ruff format)"
	@echo "  make check  - Run format check without modifying"
	@echo "  make test   - Run pytest"

lint:
	ruff check code/

format:
	black code/
	ruff check --fix code/

check:
	black --check code/
	ruff check code/

test:
	pytest code/tests/
