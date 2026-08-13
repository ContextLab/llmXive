# Test Suite Documentation

This directory contains the test suite for the PROJ-546 molecular properties pipeline.

## Structure

- `unit/`: Tests for individual functions and modules.
- `integration/`: Tests for component interactions (e.g., download -> validate -> process).
- `contract/`: Tests verifying compliance with `spec.md` requirements.

## Running Tests

```bash
python -m pytest code/tests/ -v
```

## Dependencies

Ensure `pytest` is installed in your environment.
