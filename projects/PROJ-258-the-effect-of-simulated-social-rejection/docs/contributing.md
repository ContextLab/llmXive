# Contributing Guide

## Code Style

This project follows the following code style guidelines:

- **Formatting**: Use `black` with line length 120.
- **Linting**: Use `flake8` with the provided `.flake8` configuration.
- **Type Hints**: Prefer type hints for all function signatures.
- **Documentation**: All public functions must have docstrings.

## Running Tests

Before submitting a PR, ensure all tests pass:

```bash
pytest tests/ -v
```

## Adding New Features

1. Create a new task in `tasks.md` for the feature.
2. Implement the feature in the appropriate module.
3. Add unit tests in `tests/`.
4. Update documentation in `docs/` if necessary.
5. Ensure the full pipeline runs successfully.

## Submitting Changes

1. Fork the repository.
2. Create a feature branch from `main`.
3. Make your changes and commit with clear messages.
4. Push to your fork and open a Pull Request.
5. Address any review feedback.

## Reporting Issues

Use the GitHub issue tracker to report bugs or suggest features. Include:
- A clear description of the issue.
- Steps to reproduce.
- Expected vs. actual behavior.
- Environment details (Python version, OS).
