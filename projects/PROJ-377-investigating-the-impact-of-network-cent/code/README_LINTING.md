# Linting and Formatting Setup

This project uses the following tools for code quality:

1. **Black**: Opinionated code formatter.
2. **flake8**: Linting for style and error checking.
3. **isort**: Automatic import sorting.
4. **pre-commit**: Git hooks to enforce checks before commits.

## Installation

Ensure dependencies are installed:
```bash
pip install black flake8 isort pre-commit
```

## Setup Pre-commit Hooks

Run the following in the `code/` directory:
```bash
pre-commit install
```

## Manual Execution

Format code:
```bash
black.
isort.
```

Lint code:
```bash
flake8.
```

Configuration files:
- `pyproject.toml`: Contains Black, isort, and pytest settings.
- `.flake8`: Contains flake8 settings.
- `.pre-commit-config.yaml`: Defines the pre-commit hooks.