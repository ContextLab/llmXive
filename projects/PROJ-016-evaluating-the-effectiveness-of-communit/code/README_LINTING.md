# Linting and Formatting Setup

This project uses **Ruff** for linting and **Black** for formatting.
Configuration is managed in `pyproject.toml` and `.ruff.toml`.

## Installation

Ensure you have the dev dependencies installed:
```bash
pip install -e ".[dev]"
```

## Usage

### Linting
Run Ruff to check for errors and potential fixes:
```bash
ruff check code/
```

### Formatting
Run Black (via Ruff's formatter or Black directly) to format code:
```bash
black code/
# OR via ruff
ruff format code/
```

### Pre-commit
To run checks automatically before committing:
```bash
pip install pre-commit
pre-commit install
```