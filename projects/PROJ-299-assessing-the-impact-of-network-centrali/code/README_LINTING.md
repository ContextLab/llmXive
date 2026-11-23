# Linting and Formatting Configuration

This project uses **Ruff** and **Black** for code quality, with **flake8** as a legacy compatibility layer.

## Tools

- **Black**: Opinionated code formatter (line length 88).
- **Ruff**: Extremely fast Python linter (replaces flake8, isort, pyupgrade).
- **Flake8**: Included for compatibility with existing CI tools; configured to align with Ruff/Black.
- **Mypy**: Static type checker (optional, see mypy.ini if added).

## Configuration Files

- `pyproject.toml`: Contains Black and Ruff settings.
- `.ruff.toml`: Extended Ruff configuration (lint rules, ignores).
- `.flake8`: Flake8 configuration (ignores E501 to avoid conflicts with Black).
- `Makefile`: Convenience targets for linting and formatting.

## Usage

### Format Code
```bash
make format
# or
black code/
ruff check --fix code/
```

### Check Formatting
```bash
make format-check
# or
black --check code/
```

### Lint Code
```bash
make lint
# or
ruff check code/
flake8 code/
```

## Rules

- **Line Length**: 88 characters (Black standard).
- **Target Version**: Python 3.10.
- **Ignored Rules**: E501 (line too long) is ignored in linting as Black handles line wrapping.
- **First Party**: `code` is treated as the first-party namespace for imports.

## CI Integration

Add the following to your CI pipeline:
```yaml
lint:
 - pip install -r requirements-dev.txt
 - make lint
 - make format-check
```
