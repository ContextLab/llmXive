# Contributing to llmXive

## Development Workflow

1. **Fork and Clone**: Create your own fork of the repository.
2. **Branch**: Create a new branch for your feature or bug fix (e.g., `feature/us2-execution`).
3. **Implement**: Follow the coding standards and task descriptions in `tasks.md`.
4. **Test**: Ensure all tests pass (`pytest tests/ -v`).
5. **Lint**: Run `ruff check.` to ensure code quality.
6. **Commit**: Write clear commit messages referencing the task ID (e.g., `T041: Add documentation`).

## Code Standards

- **Formatting**: We use `Black` (configured in `pyproject.toml`) and `Ruff` for linting.
- **Imports**: Import only from the defined API surface. Do not invent new names in `code/config.py` or other modules unless adding them as part of the task.
- **Data Integrity**: Never fabricate data. If a real data source is unavailable, the code must fail loudly with a clear error message.
- **Determinism**: Always seed random number generators using `config.SEED`.

## Task Implementation

- Refer to `tasks.md` for the current list of tasks.
- Tasks are grouped by User Story (US1, US2, US3).
- Complete tasks in priority order (P1 -> P2 -> P3).
- Do not implement multiple tasks in a single PR unless they are strictly dependent.

## Testing

- **Unit Tests**: Located in `tests/unit/`.
- **Integration Tests**: Located in `tests/integration/`.
- **Benchmarks**: Located in `tests/bench_sweep.py`.

Run tests before submitting a PR:
```bash
pytest tests/ -v
```

## Documentation

- Update `README.md` if you add new features or change CLI arguments.
- Add or update documentation in `docs/` for new components.
- Ensure `quickstart.md` remains accurate.

## Pull Request Process

1. Ensure all tests pass and linting is clean.
2. Update documentation as needed.
3. Link the PR to the relevant task in `tasks.md` (e.g., `[X] T041`).
4. Request review from maintainers.
