# Development Guide for PROJ-405

## Linting and Formatting

This project uses **Black** for code formatting and **Ruff** (with a fallback to **Flake8**) for linting.

### Setup
1. Ensure you are in the `code/` directory.
2. Install development dependencies:
 ```bash
 pip install -e ".[dev]"
 ```

### Commands
- **Format Code**: `make format` (or `black code/ tests/` and `ruff check --fix code/ tests/`)
- **Check Formatting**: `make format-check`
- **Lint Code**: `make lint` (or `ruff check code/ tests/` and `flake8 code/ tests/`)

### Configuration Files
- `.ruff.toml`: Ruff configuration
- `.flake8`: Flake8 configuration (if used in CI)
- `pyproject.toml`: Contains Black and Pytest settings

## Pre-commit Hooks (Optional)
To enforce these rules before every commit, you can install `pre-commit`:
```bash
pip install pre-commit
pre-commit install
```
(Note: A `.pre-commit-config.yaml` can be added in the root if desired).

## Contributing
Before submitting a PR, ensure:
1. Your code passes `make lint`.
2. Your code is formatted with `make format`.
3. All tests pass with `make test`.