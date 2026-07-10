# Test Suite Documentation

This directory contains the comprehensive test suite for the Statistical Analysis of Publicly Available Stack Overflow Question Tags project.

## Structure

- `unit/`: Unit tests for individual functions and modules
- `integration/`: End-to-end pipeline tests
- `contract/`: Schema validation tests against specifications

## Running Tests

```bash
# From project root
pytest tests/ -v

# Run specific test category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/contract/ -v

# With coverage
pytest tests/ --cov=code --cov-report=html
```

## Test Requirements

Tests require the project dependencies to be installed:

```bash
pip install -r code/requirements.txt
pip install pytest pytest-cov
```