# Test Suite for PROJ-340

This directory contains the test suite for the Gut Microbiome and Sleep Architecture correlation project.

## Structure

- `contract/`: Contract tests verifying adherence to schemas and specifications (e.g., `test_dataset_schema.py`).
- `unit/`: Unit tests for individual functions and components (e.g., `test_ingest_utils.py`, `test_analysis_utils.py`).
- `integration/`: Integration tests verifying interactions between components (e.g., `test_missing_variable.py`, `test_pipeline_flow.py`).

## Running Tests

Ensure you are in the project root directory.

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/

# Run specific test file
pytest tests/contract/test_dataset_schema.py

# Run with coverage
pytest tests/ --cov=code --cov-report=term-missing
```

## Notes

- Tests rely on `data/config/required_variables.yaml` being present.
- Some integration tests may require `data/raw/synthetic_test_data.csv` if specific real-data paths are hardcoded, but most generate data in-memory.
- The `conftest.py` file automatically adds the `code/` directory to the Python path.