# Contributing Guidelines

## Code Style
- **Formatting**: Use `black` for code formatting.
- **Linting**: Use `ruff` for linting.
- **Type Hints**: All functions must have type hints.
- **Docstrings**: Use Google-style docstrings.

## Testing
- Write unit tests for all new functions in `tests/unit/`.
- Integration tests must pass before merging.
- No synthetic data in tests unless explicitly mocking external APIs.

## Git Workflow
- Create a feature branch for each task (e.g., `feat/T037-docs`).
- Commit messages must follow the format: `[T-ID] Description`.
- PRs require at least one review.

## Documentation
- Update `README.md` if new dependencies or steps are added.
- Update `docs/` for any significant changes to the pipeline.
- Ensure all SCRs are documented in `docs/`.

## Data Handling
- **Never commit large data files** to the repository.
- Use `.gitignore` to exclude `data/raw/`, `data/interim/`, and `data/processed/`.
- Always use the `datasets` library for fetching data.
