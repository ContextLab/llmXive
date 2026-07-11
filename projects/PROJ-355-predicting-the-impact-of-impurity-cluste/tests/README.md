# Testing Guide

This directory contains the test suite for the PROJ-355-predicting-the-impact-of-impurity-cluste project.

## Structure

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests for component interactions
- `conftest.py`: Shared pytest fixtures and configuration

## Running Tests

### Unit Tests
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### All Tests
```bash
pytest tests/ -v
```

### With Coverage
```bash
pytest tests/ --cov=code --cov-report=html
```

## Prerequisites

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Adding New Tests

1. Create a new test file in the appropriate directory (`unit/` or `integration/`)
2. Follow the naming convention: `test_<module_name>.py`
3. Use descriptive test function names: `test_<function>_<scenario>`
4. Add appropriate fixtures in `conftest.py` if needed
5. Ensure tests are isolated and can run in any order