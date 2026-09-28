.PHONY: lint format check all clean

# Linting and Formatting
LINT_CMD := ruff check code/
FORMAT_CMD := black --check code/
FORMAT_WRITE_CMD := black code/

lint:
    $(LINT_CMD)

format:
    $(FORMAT_CMD)

format-write:
    $(FORMAT_WRITE_CMD)

check: lint format

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} + || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + || true
    find . -type f -name "*.pyc" -delete || true
    find . -type f -name ".DS_Store" -delete || true
    rm -rf .pytest_cache .ruff_cache data/metrics/*.csv state/projects/*.yaml 2>/dev/null || true

all: check
