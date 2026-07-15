# llmXive DanceOPD Extension - Codebase

This directory contains the implementation code for extending the DanceOPD model.

## Prerequisites

Ensure you have installed the dependencies listed in `requirements.txt` or installed via `pip install -e.[dev]`.

## Development Setup

### Formatting and Linting

We use `black` for code formatting and `ruff` for linting.

To format your code:
```bash
make format
# Or: black code/
```

To lint your code:
```bash
make lint
# Or: ruff check code/
```

To automatically fix linting issues:
```bash
make lint-fix
# Or: ruff check --fix code/
```

### Running Tests

```bash
make test
# Or: pytest tests/ -v
```

## Configuration

See `ruff.toml` for linting rules and `pyproject.toml` for project metadata and dependencies.