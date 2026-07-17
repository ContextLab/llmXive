# Testing Guide

## Directory Structure

- `unit/`: Tests for individual functions and classes
- `integration/`: Tests for component interactions
- `contract/`: Schema and API contract compliance tests

## Running Tests

```bash
# Run all tests
pytest

# Run specific test type
pytest -m unit
pytest -m integration
pytest -m contract

# Run with coverage
pytest --cov=code --cov-report=html

# Run specific test file
pytest tests/unit/test_example.py
```

## Test Markers

- `unit`: Fast, isolated tests
- `integration`: Tests requiring multiple components
- `contract`: Schema validation tests
- `slow`: Tests that take longer to run
