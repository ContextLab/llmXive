# Testing Guide

## Test Structure
- **Unit Tests**: `tests/unit/` - Test individual functions and modules.
- **Integration Tests**: `tests/integration/` - Test end-to-end workflows.

## Running Tests
```bash
pytest tests/unit/
pytest tests/integration/
```

## Coverage
Aim for >80% code coverage.

## Edge Cases
- **Missing Metadata**: Tests for handling missing metadata gracefully.
- **High Collinearity**: Tests for VIF calculation and collinearity flagging.
- **Convergence Failures**: Tests for LMM retry logic.

## Continuous Integration
Tests are run automatically on every commit via pre-commit hooks.

## Manual Testing
- Run `python code/validation/validate_quickstart.py` for full pipeline validation.
- Check `reports/pii_scan.json` for PII leaks.
