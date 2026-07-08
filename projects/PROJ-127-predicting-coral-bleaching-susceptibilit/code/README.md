# Code Directory Setup

This directory contains the core implementation for the Coral Bleaching Susceptibility project.

## Linting and Formatting

We use **Ruff** for linting and **Black** for formatting.

### Installation

Ensure dependencies are installed:
```bash
pip install -r../requirements.txt
```

### Pre-commit Hooks

To ensure code quality on every commit, install the pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

### Manual Execution

Run linter:
```bash
ruff check.
```

Run formatter:
```bash
black.
```

Or use the combined ruff format command:
```bash
ruff format.
```

## Configuration

Linting rules are defined in `.ruff.toml`.
Formatting rules are defined in `pyproject.toml` (Black section) and `.ruff.toml`.