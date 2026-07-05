# Testing Guide

## Overview

This guide explains how to test the "Assessing the Impact of Data Resolution on Statistical Power" pipeline.

## Test Structure

- **Unit Tests**: Located in `tests/unit/`. Test individual functions.
- **Integration Tests**: Located in `tests/integration/`. Test component interactions.
- **End-to-End Tests**: Located in `tests/e2e/`. Test the full pipeline.

## Running Tests

```bash
pytest tests/ -v
```

## Test Coverage

- **data_ingestion.py**: Download success, checksum validation.
- **resampling.py**: Nearest-neighbor logic, memory management.
- **analysis.py**: Moran's I calculation, null/alternative simulation, power calculation.
- **visualization.py**: Threshold identification, plotting.
- **sensitivity_analysis.py**: Sweep logic, stability confirmation.

## Writing Tests

1. **Import the module** to be tested.
2. **Create a test function** with a descriptive name.
3. **Use assertions** to verify expected behavior.
4. **Use fixtures** for common setup/teardown.

Example:
```python
def test_nearest_neighbor_preserves_integers():
 # Test logic
 assert True
```

## Continuous Integration

Tests are run automatically on GitHub Actions on every push.

## Troubleshooting Tests

- **Import errors**: Ensure dependencies are installed.
- **File not found**: Verify data paths in `config.py`.
- **Memory errors**: Reduce test data size or increase RAM.
