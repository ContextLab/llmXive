# Testing Documentation

## Test Strategy

The project employs a multi-level testing strategy:
1. **Unit Tests**: Validate individual functions and classes.
2. **Integration Tests**: Verify interactions between components (e.g., data pipeline -> model training).
3. **End-to-End Tests**: Run the full pipeline to ensure system-level correctness.

## Running Tests

### Prerequisites
Ensure `pytest` is installed:
```bash
pip install pytest
```

### Execute All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v
```

## Test Coverage

### Unit Tests
- **Data Processing**:
 - `tests/unit/test_preprocess.py`: SMILES validation, feature extraction.
 - `tests/unit/test_split.py`: Stratified splitting logic.
- **Models**:
 - `tests/unit/test_gnn_arch.py`: MPNN architecture validation (CPU-only).
- **Statistics**:
 - `tests/unit/test_stats.py`: T-test and power analysis logic.
- **Visualization**:
 - `tests/unit/test_viz.py`: Plot generation and file integrity.

### Integration Tests
- **Baseline Pipeline**:
 - `tests/integration/test_baseline_pipeline.py`: Full RF training and evaluation.
- **GNN Pipeline**:
 - `tests/integration/test_gnn_training.py`: GNN training with early stopping.

## Continuous Integration

Tests are automatically run on every push to the main branch.
- **Status**: [![CI Status](https://img.shields.io/badge/CI-Passing-brightgreen)]()
- **Coverage**: Target > 80%

## Test Data

Tests use a subset of the ESOL dataset or mock data where appropriate to ensure speed and reliability.
- **Mock Data**: Used for unit tests to avoid network dependencies.
- **Real Data**: Used for integration tests to verify end-to-end correctness.

## Debugging

If a test fails:
1. Check the error message in the test output.
2. Verify the input data and configuration.
3. Run the specific test with verbose output: `pytest tests/<file>.py -v -s`.
4. Inspect logs in `data/logs/` for detailed execution traces.
