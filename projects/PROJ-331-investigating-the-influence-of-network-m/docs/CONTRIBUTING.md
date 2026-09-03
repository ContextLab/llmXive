# Contributing to the Network Motif Analysis Pipeline

This document outlines the standards for contributing to the project.

## Code Style

- **Formatting**: Use `black` for Python code.
- **Linting**: Run `flake8` before committing.
- **Imports**: Follow the existing API surface in `code/*.py`. Do not invent new function names; extend existing modules.

## Testing

- All new features must include unit tests in `tests/unit/`.
- Integration tests in `tests/integration/` must pass.
- Tests must run on real data (or mocked real data structures) without synthetic fallbacks.

## Documentation

- Update `docs/README.md` and `docs/usage_guide.md` for any significant changes.
- Document new configuration options in `code/config.py`.

## Commit Messages

- Use the format: `[T<ID>] <Description>`.
- Example: `[T040] Add documentation for pipeline usage`.

## Workflow

1. Fork the repository.
2. Create a feature branch.
3. Implement the task (one task per branch).
4. Run tests and validation.
5. Submit a Pull Request.
