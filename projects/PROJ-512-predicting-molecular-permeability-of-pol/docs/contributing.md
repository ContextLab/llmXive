# Contributing Guide

## Code Style
- **Formatting**: Black (line-length=100)
- **Linting**: Ruff (E, F, W, I)
- **Type Hints**: Required for all function signatures.

## Testing
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Run tests: `pytest tests/`

## Adding New Features
1. Create a new task in `tasks.md`.
2. Implement in the appropriate module under `code/`.
3. Update `docs/` if new data or features are introduced.
4. Ensure all tests pass before merging.

## Documentation Standards
- All new modules must have a docstring.
- Data features must be added to `docs/data_dictionary.md`.
- API changes must be reflected in `docs/api_reference.md`.
