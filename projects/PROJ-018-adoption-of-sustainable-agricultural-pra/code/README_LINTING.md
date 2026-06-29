# Linting and Formatting Configuration

This project uses **ruff** for linting and **black** for code formatting.

## Installation

Ensure you have the development dependencies installed:

```bash
pip install -e ".[dev]"
```

Or install explicitly:

```bash
pip install ruff black
```

## Usage

### Formatting

Format all Python files in the `code/` directory:

```bash
black code/
```

Or use the Makefile:

```bash
make format
```

### Linting

Check for lint errors without fixing:

```bash
ruff check code/
```

Or use the Makefile:

```bash
make lint
```

### Check Both

To run both checks:

```bash
make check
```

## Configuration

- **Black**: Configured in `pyproject.toml` with a line length of 88 and Python 3.11 target.
- **Ruff**: Configured in `ruff.toml` and `pyproject.toml`. It checks for errors, warnings, and best practices (E, W, F, I, B, C4, UP).
- **Line Length**: Set to 88 characters to align with Black's default.
- **Target Version**: Python 3.11.

## Pre-commit (Optional)

To automatically format and lint before commits, you can set up a pre-commit hook:

1. Install pre-commit: `pip install pre-commit`
2. Create `.pre-commit-config.yaml` in the project root:

```yaml
repos:
 - repo: https://github.com/psf/black
 rev: 23.1.0
 hooks:
 - id: black
 args: ["--config", "code/pyproject.toml"]
 - repo: https://github.com/astral-sh/ruff-pre-commit
 rev: v0.1.0
 hooks:
 - id: ruff
 args: ["--config", "code/ruff.toml"]
```

3. Run `pre-commit install`.