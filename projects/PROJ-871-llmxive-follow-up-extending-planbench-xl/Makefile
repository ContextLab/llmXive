.PHONY: lint format check install-dev test

install-dev:
    pip install -e ".[dev]"
    # If using the explicit requirements from T001b:
    # pip install -r requirements.txt
    # pip install flake8 black isort pre-commit pytest

lint:
    flake8 code/ tests/
    isort --check-only code/ tests/

format:
    black code/ tests/
    isort code/ tests/

check: lint

test:
    pytest tests/ -v

pre-commit-install:
    pre-commit install

pre-commit-run:
    pre-commit run --all-files