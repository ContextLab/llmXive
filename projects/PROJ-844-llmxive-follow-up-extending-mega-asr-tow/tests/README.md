# Unit Tests for llmXive

## Running Tests

```bash
pytest tests/
```

## Structure

- `tests/unit/`: Unit tests for individual modules
- `tests/conftest.py`: Shared fixtures and configuration

## Coverage

- `test_config.py`: Configuration loading and validation
- `test_data_loader.py`: Data fetching, hashing, and stratified sampling
- `test_models.py`: Entity class instantiation and serialization
- `test_metrics.py`: Metric calculation framework
