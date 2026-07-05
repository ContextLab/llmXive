# Code Quality Configuration

This project uses `black` for formatting, `flake8` for linting, and `ruff` as a fast alternative linter.
`pre-commit` hooks are configured to enforce these standards automatically.

## Setup

1. Install development dependencies:
 ```bash
 pip install -r requirements-dev.txt
 ```

2. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Usage

### Manual Checks
```bash
# Run black
black code/

# Run flake8
flake8 code/

# Run ruff
ruff check code/
```

### Pre-commit
Run all hooks on all files:
```bash
pre-commit run --all-files
```

## Configuration
- **Black**: 88 char line length, Python 3.11 target.
- **Flake8**: 88 char line length, ignores E203 (black conflict), E266, W503.
- **Ruff**: Includes E, W, F, I, C, B, UP, ARG, PL rules. Ignores black-conflicting rules.
- **Pytest**: Configured for `tests/` directory with markers for slow/integration tests.