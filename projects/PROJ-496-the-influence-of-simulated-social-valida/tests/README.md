# Tests Directory

This directory contains the test suite for the `PROJ-496` research pipeline.

## Structure

- `test_search.py`: Tests for dataset discovery and eligibility (US1).
- `test_preprocess.py`: Tests for EEG preprocessing and P300 extraction (US2).
- `test_analyze.py`: Tests for statistical modeling and sensitivity analysis (US3).

## Running Tests

Ensure you are in the project root directory and run:

```bash
pytest tests/
```

## Requirements

- `pytest`
- Dependencies listed in `requirements.txt`
