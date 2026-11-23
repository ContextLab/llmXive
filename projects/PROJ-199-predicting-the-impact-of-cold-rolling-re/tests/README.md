# Tests Directory

This directory contains all tests for the project.

## Structure

- `unit/`: Unit tests for individual functions and classes
- `integration/`: Integration tests for module interactions
- `contract/`: Contract tests for API compliance
- `conftest.py`: Pytest configuration and shared fixtures

## Running Tests

```bash
pytest tests/
```

To run with coverage:
```bash
pytest tests/ --cov=code --cov-report=html
```