# Makefile for PROJ-055
# Common linting and formatting commands

.PHONY: lint-python lint-r format-python format-r lint format clean check-all

# Python Linting
lint-python:
	ruff check code/
	black --check code/

# R Linting
lint-r:
	Rscript -e "lintr::lint_package('code/R')"

# Python Formatting
format-python:
	black code/
	ruff check --fix code/

# R Formatting (requires styler)
format-r:
	Rscript -e "styler::style_dir('code/R', recursive = TRUE)"

# Full Lint
lint: lint-python lint-r

# Full Format
format: format-python format-r

# Run all checks
check-all: lint

# Clean temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf logs/*.log
	rm -rf results/*.csv
	rm -rf results/*.png
	rm -rf data/processed/*.csv
	rm -rf data/phylogeny/*.newick
	rm -rf data/raw/*.csv
	rm -rf data/raw/*.tar.gz
	rm -rf data/raw/*.zip
	rm -rf data/raw/*.json
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/