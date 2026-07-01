# PROJ-472: Investigating the Impact of Network Structure on Neural Avalanche Dynamics

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

3. Initialize pre-commit hooks (optional but recommended):
 ```bash
 pip install pre-commit
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

To format and fix linting issues automatically:
```bash
ruff check --fix code/ tests/
black code/ tests/
```