# Linting and Formatting Configuration

This project uses **Ruff** for linting and **Black** for formatting, configured via `pyproject.toml` (or separate config files as implemented).

## Setup

1. Install development dependencies:
 ```bash
 pip install -r code/requirements-dev.txt
 ```
2. (Optional) Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Usage

### Manual Run
Lint the codebase:
```bash
ruff check code/
```

Format the codebase:
```bash
black code/
```

### Pre-commit
Run all hooks on staged files:
```bash
pre-commit run --all-files
```

## Configuration
- **Ruff**: Configured in `code/.ruff.toml`. Ignores line-length (handled by Black) and allows `assert` in tests.
- **Black**: Configured in `code/.black.toml`. Line length 88, target Python 3.11.