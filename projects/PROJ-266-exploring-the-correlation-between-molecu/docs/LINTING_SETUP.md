# Linting and Formatting Configuration

This project uses `black` for code formatting, `flake8` for linting, and `isort` for import sorting.
Pre-commit hooks are configured to enforce these standards before every commit.

## Installation

1. Install development dependencies:
 ```bash
 pip install -e ".[dev]"
 ```

2. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Usage

### Manual Execution
Run formatters and linters manually:
```bash
# Format code
black code/ tests/
isort code/ tests/

# Lint code
flake8 code/ tests/
```

### Pre-commit Hooks
Hooks run automatically on `git commit`. To run all hooks on all files:
```bash
pre-commit run --all-files
```

## Configuration Files

- `.flake8`: Flake8 rules and exclusions
- `pyproject.toml`: Black and isort settings
- `.pre-commit-config.yaml`: Pre-commit hook definitions

## Exclusions

The following are excluded from linting/formatting:
- `.git`, `__pycache__`, `build`, `dist`, `.eggs`, `*.egg-info`, `.venv`, `venv`
- `tests/` files have relaxed rules for fixtures and type hints
- `__init__.py` files allow unused imports for public API exposure