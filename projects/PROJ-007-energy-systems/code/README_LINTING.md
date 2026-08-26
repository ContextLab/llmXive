# Linting and Formatting Guide

This project uses **Ruff** for linting and **Black** for code formatting to ensure consistency across the codebase.

## Installation

1. Ensure you are in the project root (`code/`).
2. Install development dependencies:
 ```bash
 pip install -r requirements-dev.txt
 ```
3. Install pre-commit hooks to automatically format and lint on every commit:
 ```bash
 pre-commit install
 ```

## Manual Execution

### Linting
Run Ruff to check for errors and style violations:
```bash
ruff check.
```
To automatically fix fixable issues:
```bash
ruff check --fix.
```

### Formatting
Run Black to format code:
```bash
black.
```

### Combined Check
Run the combined check script (simulates CI):
```bash
./scripts/setup_linting.sh
```

## Configuration
- **Ruff**: Configured in `.ruff.toml`. Ignores line length (handled by Black) and allows asserts in tests.
- **Black**: Configured in `.black.toml`. Line length set to 88, targeting Python 3.11.
- **Pre-commit**: Configured in `.pre-commit-config.yaml` to run both tools before every commit.