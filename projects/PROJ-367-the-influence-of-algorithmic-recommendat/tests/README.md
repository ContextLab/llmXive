# Testing Guide for PROJ-367

This directory contains the test suite for the "Influence of Algorithmic Recommendations" project.

## Running Tests

Ensure you are in the project root directory:

```bash
cd projects/PROJ-367-the-influence-of-algorithmic-recommendat
```

Install dependencies (if not already done):

```bash
pip install -r code/requirements.txt
pip install pytest
```

Run all tests:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run specific test file:

```bash
pytest tests/unit/test_metrics.py
```

Run only unit tests:

```bash
pytest -m unit
```

## Test Structure

- `unit/`: Unit tests for individual functions (metrics, ingestion, modeling, robustness).
- `integration/`: Integration tests for end-to-end workflows.
- `conftest.py`: Shared fixtures and configuration.

## Coverage

To generate a coverage report:

```bash
pip install pytest-cov
pytest --cov=code --cov-report=html
```

Open `htmlcov/index.html` in your browser to view the report.
