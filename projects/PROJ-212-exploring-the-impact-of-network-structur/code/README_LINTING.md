# Linting and Formatting Configuration

This project uses **Ruff** for linting and **Black** for code formatting.

## Tools

- **Ruff**: A fast Python linter written in Rust. Replaces flake8, isort, and others.
- **Black**: The uncompromising Python code formatter.

## Configuration

- **Ruff**: Configured in `.ruff.toml`.
- **Black**: Configured in `pyproject.toml` under `[tool.black]`.
- **Pytest**: Configured in `pyproject.toml` under `[tool.pytest.ini_options]`.

## Usage

### Formatting

To format code automatically:

```bash
black code/
```

### Linting

To check for linting errors:

```bash
ruff check code/
```

### Fixing Issues

Ruff can automatically fix many issues:

```bash
ruff check --fix code/
```

### Pre-commit Hooks (Optional)

To run these checks before every commit, install `pre-commit` and add a `.pre-commit-config.yaml`:

```yaml
repos:
 - repo: https://github.com/astral-sh/ruff-pre-commit
 rev: v0.1.6
 hooks:
 - id: ruff
 args: [ --fix ]
 - repo: https://github.com/psf/black
 rev: 23.11.0
 hooks:
 - id: black
```

## Rules

- Line length is set to 88 characters (Black default).
- Target Python version is 3.11.
- Isort is configured to recognize project modules as first-party.
- Assertions are allowed in test files.
- Unused imports are allowed in `__init__.py` files to facilitate API exposure.