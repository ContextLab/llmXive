# Contribution Guidelines

## Code Style

- **Formatting**: All Python code must be formatted with `black`.
- **Linting**: All code must pass `ruff` checks.
- **Imports**: Follow the import order: standard library, third-party, local project.
- **Line Length**: Max 88 characters per line (enforced by black).

## Running Checks Before Commit

Please run the following before committing:

```bash
make format-write
make lint
pytest tests/
```

## Pull Requests

- Ensure all tests pass.
- Ensure `make check` passes.
- Update documentation if necessary.