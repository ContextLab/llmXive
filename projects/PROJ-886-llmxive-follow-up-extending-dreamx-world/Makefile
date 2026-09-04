.PHONY: install format lint test clean

install:
    pip install -e .

format:
    black projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/
    black projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/
    ruff check --fix projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/
    ruff check --fix projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/

lint:
    ruff check projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/
    ruff check projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/
    black --check projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/code/
    black --check projects/PROJ-886-llmxive-follow-up-extending-dreamx-world/tests/

test:
    pytest tests/ -v

clean:
    find . -type d -name "__pycache__" -exec rm -r {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type d -name ".pytest_cache" -exec rm -r {} +
    find . -type d -name ".ruff_cache" -exec rm -r {} +
    find . -type d -name ".mypy_cache" -exec rm -r {} +
