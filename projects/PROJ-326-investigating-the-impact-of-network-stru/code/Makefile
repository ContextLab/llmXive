.PHONY: lint format check test

# Run linter
lint:
	cd code && ruff check .

# Run formatter (dry run to check)
check-format:
	cd code && black --check .

# Format code
format:
	cd code && black .
	cd code && ruff check . --fix

# Run tests
test:
	cd code && pytest tests/ -v

# Full CI check
ci: lint check-format test
	@echo "All checks passed"
