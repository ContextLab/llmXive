# Testing Guide

This directory contains the test suite for the Statistical Analysis of Publicly Available Election Poll Aggregates project.

## Test Structure

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests for component interactions
- `contract/`: Contract tests for API and data schema compliance

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_config.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_config.py::test_config_module_structure
```

## Test Conventions

- All test files start with `test_`
- Test functions start with `test_`
- Unit tests test individual functions/classes
- Integration tests test component interactions
- Contract tests verify API/data schema compliance

## Fixtures

Common fixtures are defined in `conftest.py`:

- `temp_data_dir`: Temporary directory for file-based tests
- `sample_poll_data`: Sample poll data structure
- `add_src_to_path`: Automatically adds src/ to sys.path

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Tests
 run: pytest --verbose --cov=src
```