# Testing Guide

## Overview

This project includes unit and integration tests to verify correctness. Tests are located in `tests/`.

## Running Tests

```bash
pytest tests/
```

## Test Structure

### Unit Tests

- `tests/unit/test_config.py`: Validates configuration management.
- `tests/unit/test_stability.py`: Checks L2 error and max diff calculations.
- `tests/unit/test_stats.py`: Verifies Welch's t-test implementation.

### Integration Tests

- `tests/integration/test_compile_run.py`: Ensures compilation and execution work end-to-end.
- `tests/integration/test_stability_flow.py`: Tests the full stability analysis pipeline.
- `tests/integration/test_viz.py`: Validates Pareto frontier generation.

## Test Coverage

- **Configuration**: Invalid flag rejection, valid flag acceptance.
- **Compilation**: Compiler availability, binary hashing.
- **Execution**: Latency measurement, memory fallback.
- **Stability**: NaN detection, error calculation, threshold flagging.
- **Statistics**: Block averaging, t-test significance.
- **Visualization**: Plot generation, data filtering.

## Writing New Tests

1. Create a new test file in `tests/unit/` or `tests/integration/`.
2. Use `pytest` fixtures for setup/teardown.
3. Follow the Red-Green-Refactor cycle: write a failing test first.
4. Ensure tests are independent and reproducible.

## Continuous Integration

Tests should pass on every commit. Configure your CI pipeline to run:

```bash
pytest tests/ --cov=code
```

## Troubleshooting Tests

- **Compiler Not Found**: Ensure GCC 11+ or Clang 14+ is installed.
- **Memory Errors**: Reduce tensor dimensions in test config.
- **Floating Point Issues**: Use `pytest.approx()` for float comparisons.
