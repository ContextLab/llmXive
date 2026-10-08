# Test Suite for PROJ-066

This directory contains the unit and integration tests for the molecular descriptor correlation project.

## Running Tests

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
pytest
```

## Test Structure

- `test_preprocess.py`: Tests for data cleaning, filtering, and descriptor calculation.
- `test_models.py`: Tests for model training, splitting, and metric calculation.
- `test_evaluation.py`: Integration tests for the full evaluation pipeline.
- `conftest.py`: Shared fixtures and configuration.

## Coverage

These tests verify:
1. Correctness of data preprocessing steps.
2. Model training success and artifact generation.
3. Metric calculation accuracy.
4. Memory safety and resource constraints (via logic checks).