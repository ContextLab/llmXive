# Test Suite

This directory contains the test suite for the Plant Phenology Prediction Pipeline.

## Structure

- `contract/`: Tests validating data schemas and API contracts against specifications.
- `data/`: Tests for data ingestion, preprocessing, and storage utilities.
- `integration/`: Tests verifying end-to-end pipeline stages.
- `unit/`: Tests for individual functions and components.

## Running Tests

```bash
pytest tests/
```

## Coverage

To generate a coverage report:

```bash
pytest tests/ --cov=src --cov-report=html
```