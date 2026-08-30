# Unit Tests for PROJ-483

This directory contains unit tests for the dependency injection and simulation logic.

## Structure

- `__init__.py`: Package marker
- `conftest.py`: Shared pytest configuration and fixtures
- `test_dependency_injector_fixtures.py`: Mock data fixtures for testing
- `test_dependency_injector.py`: Tests for AR(1) injection logic
- `test_block_bootstrap.py`: Tests for block bootstrap logic
- `test_spatial_proxy.py`: Tests for spatial proxy generation
- `test_dependency_injector_fixtures_integration.py`: Integration tests for fixtures

## Running Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_dependency_injector.py -v

# Run with coverage
pytest tests/unit/ --cov=code --cov-report=html
```

## Test Fixtures

The `test_dependency_injector_fixtures.py` module provides:
- `create_ar1_fixture()`: Synthetic AR(1) time series
- `create_independent_fixture()`: Synthetic i.i.d. time series
- `create_block_bootstrap_fixture()`: Synthetic block-structured data
- `create_spatial_proxy_fixture()`: Synthetic feature-space data for clustering

These fixtures are used to validate the dependency injection functions without
requiring real dataset fetches or full simulation runs.

## Validation Helpers

- `assert_autocorrelation_matches()`: Verifies lag-1 autocorrelation
- `assert_block_structure_preserved()`: Verifies block bootstrap integrity
- `assert_cluster_separation()`: Verifies feature-space clustering quality