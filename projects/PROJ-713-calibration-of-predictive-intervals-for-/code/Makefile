.PHONY: lint format test clean

# Linting targets
lint:
	flake8 code/
	mypy code/

format:
	black code/
	isort code/

format-check:
	black --check code/
	isort --check-only code/

# Testing targets
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=code --cov-report=term-missing

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache htmlcov

# Full check
check: format-check lint test
	@echo "All checks passed!"