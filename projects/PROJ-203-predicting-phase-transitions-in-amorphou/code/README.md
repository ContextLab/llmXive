# PROJ-203: Predicting Phase Transitions in Amorphous Solids

## Code Quality & Formatting

This project uses **Ruff** for linting and **Black** for code formatting.

### Prerequisites
Ensure you are in the project root (`code/` directory) and have dependencies installed:
```bash
pip install -r requirements.txt
```

### Linting
Run the linter to check for code style violations and potential errors:
```bash
make lint
# or
ruff check code/ tests/
```

### Formatting
Format the code automatically:
```bash
make format
# or
black code/ tests/
```

Check formatting without modifying files:
```bash
make format-check
# or
black --check code/ tests/
```

### Full Quality Check
Run both linting and formatting checks:
```bash
make check
```

### Configuration Files
- `.ruff.toml`: Ruff configuration
- `pyproject.toml`: Black configuration and project metadata
- `.flake8`: Legacy flake8 configuration (for compatibility)
- `Makefile`: Convenience commands for quality tasks

## Testing
Run the test suite:
```bash
make test
```

## Directory Structure
- `code/`: Source code
- `data/`: Raw and processed data (gitignored)
- `models/`: Trained model artifacts (gitignored)
- `tests/`: Unit and integration tests
- `docs/`: Documentation

## Contribution Guidelines
1. Ensure code passes `make check` before committing.
2. Add tests for new functionality.
3. Update documentation as needed.