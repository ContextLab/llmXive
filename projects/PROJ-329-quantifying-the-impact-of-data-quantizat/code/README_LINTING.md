# Linting and Formatting Configuration

This project uses `flake8` for linting and `black` for code formatting, configured via `pyproject.toml`.

## Installation

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

## Setup Pre-commit Hooks

To ensure code quality on every commit:
```bash
pre-commit install
```

## Manual Execution

Run linter:
```bash
flake8 code/
```

Run formatter:
```bash
black code/
```

Run import sorter:
```bash
isort code/
```

## Configuration Details

- **Black**: Line length 88, Python 3.11 target.
- **Flake8**: Max line length 88, ignores E203, E266, W503 (compatible with Black).
- **Isort**: Profile set to black for consistent sorting.