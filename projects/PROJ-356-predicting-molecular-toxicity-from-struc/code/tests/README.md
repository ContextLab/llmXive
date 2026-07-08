# Tests

This directory contains unit and integration tests for the Molecular Toxicity Prediction Pipeline.

## Running Tests

To run all tests:
```bash
pytest
```

To run with coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

## Structure

- `unit/`: Unit tests for individual modules
- `integration/`: Integration tests for pipeline components
- `data/`: Test data fixtures (smaller, synthetic for speed)
- `conftest.py`: Shared pytest fixtures and configuration
- `__init__.py`: Package marker
