# Code Formatting and Linting Guide

This project uses **Black** for code formatting and **Ruff** for linting.

## Configuration

Configuration is managed in `pyproject.toml`:
- **Black**: Target Python 3.11, line length 88.
- **Ruff**: Enforces E, W, F, I, C, B, UP rules. Ignores E501 (handled by Black).

## Usage

### Format Code
Run the format script to apply Black formatting and auto-fix Ruff issues:
```bash
bash scripts/format.sh
```

### Lint Code
Run the lint script to check for issues without auto-fixing:
```bash
bash scripts/lint.sh
```

### Manual Commands
If running manually:
```bash
# Format
black projects/PROJ-512-predicting-molecular-permeability-of-pol/code
black projects/PROJ-512-predicting-molecular-permeability-of-pol/tests

# Lint
ruff check projects/PROJ-512-predicting-molecular-permeability-of-pol/code
ruff check projects/PROJ-512-predicting-molecular-permeability-of-pol/tests
```

## Pre-commit Hooks (Optional)
To run these checks automatically before committing, you can install `pre-commit`:
```bash
pip install pre-commit
pre-commit install
```
(Add a `.pre-commit-config.yaml` file if this feature is desired in a future task.)