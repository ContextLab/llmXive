# PROJ-019: Exploring the Mechanisms of Gene Regulation

## Setup

1. Create a virtual environment with Python 3.11:
 ```bash
 python3.11 -m venv.venv
 source.venv/bin/activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Linting and Formatting

This project uses **Black** for formatting and **Ruff** for linting.

To run manually:
```bash
# Format code
black code/ tests/

# Lint code
ruff check code/ tests/
```

Alternatively, use `pre-commit run --all-files` to run both before committing.

## Project Structure

- `code/`: Source code
- `data/`: Data files (raw, interim, processed)
- `tests/`: Test suite
- `specs/`: Feature specifications
- `pyproject.toml`: Project configuration, dependencies, and tool settings