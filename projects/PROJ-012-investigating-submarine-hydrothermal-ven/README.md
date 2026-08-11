# Submarine Hydrothermal Vent Microbial Communities Research Pipeline

## Running Integration Tests

This project includes integration tests for non-linearity detection in diversity-pH relationships.

### Prerequisites
- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`
- Development dependencies: `pip install -r requirements-dev.txt`

### Running Tests
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific non-linearity test
pytest tests/integration/test_diversity_nonlinear.py -v

# Run with coverage
pytest tests/integration/test_diversity_nonlinear.py --cov=code --cov-report=html
```

### Test Structure
- `tests/integration/test_diversity_nonlinear.py`: Tests for non-linearity detection
- `tests/integration/conftest.py`: Shared fixtures for integration tests

### What This Test Validates
1. Linear relationships are NOT flagged as non-linear
2. Quadratic non-linearity is correctly detected
3. Logarithmic non-linearity is detected
4. Random data is not flagged as non-linear
5. Warning messages are generated appropriately
6. Edge cases (small samples, constant values) are handled gracefully

## Project Structure
- `code/`: Source code modules
- `data/`: Data files (raw, processed)
- `tests/`: Test suites
- `results/`: Analysis outputs and figures
- `state/`: Runtime state and logs

## License
MIT License