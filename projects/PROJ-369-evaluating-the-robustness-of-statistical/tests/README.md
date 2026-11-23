# Tests Directory

This directory contains the test suite for the project.

## Structure

- `unit/`: Unit tests for individual functions and classes.
- `integration/`: Integration tests for full pipelines and module interactions.
- `conftest.py`: Shared pytest fixtures and configuration.

## Running Tests

```bash
pytest
```

To run with coverage:

```bash
pytest --cov=src --cov-report=term-missing
```