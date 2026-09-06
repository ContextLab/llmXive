# Contributing to Dream-State Learning

## Development Workflow

1. **Fork & Clone**: Fork the repository and clone your fork.
2. **Environment**: Create a virtual environment and install dependencies.
3. **Testing**: Run unit tests before submitting changes.
 ```bash
 pytest tests/unit/
 ```
4. **Integration**: Run integration tests to ensure the full pipeline works.
 ```bash
 pytest tests/integration/
 ```
5. **Linting**: Ensure code passes `ruff` and `black` checks.
 ```bash
 ruff check code/
 black --check code/
 ```

## Adding New Features

- **User Stories**: New features should be organized as User Stories in `tasks.md`.
- **Documentation**: Update `docs/` and `quickstart.md` for any new commands or configuration options.
- **Tests**: New features must include corresponding unit and integration tests.

## Code Style

- **Python**: Follow PEP 8.
- **Formatting**: Use `black` for consistent formatting.
- **Linting**: Use `ruff` for static analysis.
- **Type Hinting**: Use type hints for all function arguments and return values.

## Commit Messages

Use the following format:
```
[TASK-ID] Short description

Longer description if necessary.
- Reference related issues or PRs.
- Mention any breaking changes.
```

Example:
```
[T051] Add documentation for Wake/Dream cycle

- Updated quickstart.md with usage examples.
- Added architecture.md to explain data flow.
- Fixed typo in config.py comments.
```

## Review Process

- All changes must be reviewed by at least one other contributor.
- CI checks (linting, tests) must pass before merging.
- Documentation updates are mandatory for any new feature.
