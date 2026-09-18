# Contributing to PROJ-345

## Code Style
- **Formatting**: Black
- **Linting**: Ruff
- **Pre-commit**: Hooks are configured in `.pre-commit-config.yaml`

## Development Workflow
1. Create a feature branch from `main`.
2. Implement changes in `code/`.
3. Add tests in `tests/`.
4. Run `pre-commit run --all-files` before committing.
5. Ensure all tasks in `tasks.md` are completed and verified.

## Testing
- **Unit Tests**: `pytest tests/unit/`
- **Integration Tests**: `pytest tests/integration/`
- **Validation**: `python code/validation/validate_quickstart.py`

## Data Handling
- **No Synthetic Data**: All data must come from real sources (OSF/HF).
- **Human-Rated Ambiguity**: Do not implement synthetic ambiguity derivation.
- **Large Datasets**: Use chunked processing (`code/data/chunked_processor.py`) for datasets >7GB.

## Reporting Limitations
All reports must explicitly state:
- "Associational analysis only; not causal"
- "Observational nature" limitations
- "Derived prime valence" limitations

## Documentation
Update `docs/` and `quickstart.md` whenever significant changes are made to the pipeline.
