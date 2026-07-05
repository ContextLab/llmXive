# Contributing Guide

## Overview

This document outlines how to contribute to the "Assessing the Impact of Data Resolution on Statistical Power" project.

## Code Style

- **Formatting**: Use Black for Python code formatting.
- **Linting**: Use Ruff for linting.
- **Type Hinting**: Use type hints for all function signatures.

## Development Workflow

1. **Fork the repository**.
2. **Create a feature branch** based on the task you are implementing.
3. **Implement the task**:
 - Write tests first (if applicable).
 - Ensure tests fail before implementation.
 - Implement the feature.
 - Ensure tests pass.
4. **Run the full pipeline** to verify no regressions.
5. **Submit a pull request**.

## Testing

- Unit tests are located in `tests/`.
- Run tests with: `pytest tests/`
- Ensure all tests pass before submitting.

## Documentation

- Update `README.md` if new features are added.
- Add docstrings to all new functions.
- Update `docs/` if significant changes occur.

## Reporting Issues

- Use the GitHub issue tracker.
- Provide a clear description of the issue.
- Include steps to reproduce.

## License

By contributing, you agree that your contributions will be licensed under the project's license.
