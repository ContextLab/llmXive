# Makefile for PROJ-185: Predicting Protein-Protein Interactions
# Includes targets for skeleton verification and general pipeline management

.PHONY: all clean validate skeleton-check help

# Default target
all: skeleton-check

# Verify the repository skeleton (T001c / T001d)
skeleton-check:
	@echo "Checking repository skeleton..."
	@test -d src || (echo "ERROR: src/ directory missing" && exit 1)
	@test -d tests || (echo "ERROR: tests/ directory missing" && exit 1)
	@test -d data || (echo "ERROR: data/ directory missing" && exit 1)
	@test -d results || (echo "ERROR: results/ directory missing" && exit 1)
	@test -d docs || (echo "ERROR: docs/ directory missing" && exit 1)
	@test -d contracts || (echo "ERROR: contracts/ directory missing" && exit 1)
	@echo "Skeleton verification passed."

# Clean generated artifacts
clean:
	@echo "Cleaning generated artifacts..."
	@rm -rf results/*
	@rm -rf data/*
	@rm -rf state/*
	@rm -f pipeline.log
	@rm -f *.egg-info -rf
	@rm -rf __pycache__
	@rm -rf .pytest_cache
	@rm -rf .ruff_cache
	@rm -rf htmlcov
	@rm -rf .coverage
	@echo "Clean complete."

# Validate outputs (delegates to src/pipeline/validate.py)
validate:
	@echo "Validating pipeline outputs..."
	@python code/src/pipeline/validate.py

# Run tests
test:
	@echo "Running tests..."
	@cd code && python -m pytest tests/ -v

# Create skeleton (wrapper for create_skeleton.py)
create-skeleton:
	@echo "Creating repository skeleton..."
	@python code/create_skeleton.py

help:
	@echo "Available targets:"
	@echo "  all              - Run default checks (skeleton verification)"
	@echo "  skeleton-check   - Verify required directories exist"
	@echo "  clean            - Remove generated artifacts"
	@echo "  validate         - Validate pipeline outputs"
	@echo "  test             - Run unit tests"
	@echo "  create-skeleton  - Generate the repository structure"
	@echo "  help             - Show this help message"