.PHONY: lint format check test

lint:
    ruff check code/

format:
    ruff format code/
    isort code/
    black code/

check: lint format
    @echo "Running checks..."
    ruff check code/
    ruff format --check code/

test:
    pytest code/ -v

install-deps:
    pip install -r code/requirements.txt
    pip install ruff black isort pytest

setup: install-deps
    @echo "Project setup complete. Run 'make lint' and 'make test' to verify."
