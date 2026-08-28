.PHONY: lint format check

lint:
    @echo "Running flake8..."
    flake8 code/ tests/
    @echo "Running pylint..."
    pylint code/ tests/ --rcfile=pyproject.toml

format:
    @echo "Running black..."
    black code/ tests/
    @echo "Running isort..."
    isort code/ tests/

check: lint
    @echo "All checks passed."

install-dev:
    pip install flake8 black isort pylint
