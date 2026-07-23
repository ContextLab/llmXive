# Tests for llmXive Follow-up Project

This directory contains all unit and integration tests for the project.

## Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_config.py

# Run tests matching a pattern
pytest -k "test_distortion"

# Run tests with coverage report
pytest --cov=code --cov-report=html
```

## Test Structure

- `unit/`: Unit tests for individual modules and functions
- `integration/`: Integration tests for component interactions (if added later)
- `conftest.py`: Global fixtures and configuration

## Writing Tests

1. Create a new test file in `tests/unit/` with the naming convention `test_<module_name>.py`
2. Use `pytest` fixtures from `conftest.py` where applicable
3. Ensure tests are independent and can run in any order
4. Mock external dependencies (API calls, heavy computations)
5. Use descriptive test names that explain the expected behavior

## Continuous Integration

Tests are automatically run on GitHub Actions for every push and pull request.
See `.github/workflows/` for CI configuration.