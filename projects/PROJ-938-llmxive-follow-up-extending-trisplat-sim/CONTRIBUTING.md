# Contributing Guidelines

## Code Style
- Follow PEP 8 conventions
- Use `black` for formatting (`black code/`)
- Use `ruff` for linting (`ruff check code/`)
- Type hints are required for all public functions

## Testing
- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Integration tests must run on real data (no synthetic fallbacks)

## Pull Requests
1. Fork the repository
2. Create a feature branch
3. Implement changes and tests
4. Run `pytest` and `ruff check`
5. Submit PR with description of changes

## Data Hygiene
- Never commit large data files
- Use streaming loaders for datasets
- Record checksums for downloaded data
