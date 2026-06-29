# Contributing to the Project

Thank you for your interest in contributing! This project follows a structured task-based implementation strategy.

## Development Workflow

1. **Review `tasks.md`:** All work is tracked in the `tasks.md` file. Each task has a unique ID (e.g., T037).
2. **Check Dependencies:** Ensure all prerequisite tasks are completed before starting a new task.
3. **Implement:** Write code in the `code/` directory. Follow the existing API surface.
4. **Test:** Write or update tests in `tests/`. Ensure tests pass.
5. **Document:** Update documentation in `docs/` if new features or changes are made.
6. **Commit:** Commit your changes with a message referencing the task ID (e.g., "Implement T037: Documentation updates").

## Code Style

- **Formatting:** Use `black` for code formatting.
- **Linting:** Use `ruff` for linting.
- **Type Hinting:** Use Python type hints where possible.
- **Imports:** Import only from the defined API surface in `code/` modules. Do not invent new names.

## Testing

- **Unit Tests:** Located in `tests/unit/`.
- **Integration Tests:** Located in `tests/integration/`.
- **Contract Tests:** Located in `tests/unit/` (e.g., mocking external APIs).

Run tests with:
```bash
pytest tests/
```

## Documentation

- Update `README.md` for high-level changes.
- Add detailed guides to `docs/` for new features.
- Keep `tasks.md` up to date with task status.

## Reporting Issues

If you encounter a bug or have a suggestion, please open an issue on the repository. Include:
- A clear description of the problem.
- Steps to reproduce.
- Expected vs. actual behavior.
- Relevant logs or error messages.
