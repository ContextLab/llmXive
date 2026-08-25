# Test Suite for llmXive Project

This directory contains the test infrastructure for the FashionChame project.

## Directory Structure

- `unit/` - Unit tests for individual modules
- `integration/` - Integration tests for pipeline components
- `scripts/` - Standalone verification scripts
- `conftest.py` - Pytest fixtures and configuration
- `__init__.py` - Package initialization

## Running Tests

### Run all tests with pytest
```bash
cd code
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/unit/test_loader_streaming.py -v
```

### Run with coverage report
```bash
pytest tests/ --cov=src --cov-report=html
```

### Run integration tests only
```bash
pytest tests/integration/ -v
```

## Test Requirements

All tests require the project dependencies to be installed:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

## Test Conventions

- Test files are named `test_<module_name>.py`
- Test functions are named `test_<function_name>_<scenario>()`
- Test classes are named `Test<ModuleOrFeatureName>`
- Unit tests should be isolated and not require network access
- Integration tests may require real data or mock external services
