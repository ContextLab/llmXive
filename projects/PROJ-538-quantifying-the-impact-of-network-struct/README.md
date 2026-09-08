# Project README: Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

## Testing

This project uses `pytest` for testing with coverage reporting.

### Running Tests

To run the full test suite with coverage:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/unit/test_models.py
```

To run with verbose output:

```bash
pytest -v
```

### Coverage

Coverage reports are generated in `htmlcov/` (HTML) and printed to the terminal (term-missing).

## Project Structure

- `code/`: Source code modules
- `data/`: Data directories (raw, processed, contracts)
- `tests/`: Test suite
- `docs/`: Documentation
- `specs/`: Feature specifications