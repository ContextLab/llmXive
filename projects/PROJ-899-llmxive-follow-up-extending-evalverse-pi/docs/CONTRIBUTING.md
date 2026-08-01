# Contributing to llmXive

Thank you for your interest in contributing! This document outlines the process for adding features, fixing bugs, and maintaining code quality.

## Code Style
- **Formatting**: We use `black`.
- **Linting**: We use `ruff`.
- **Type Hints**: All new functions must include type hints.

## Pull Request Process
1. Fork the repository.
2. Create a branch: `feature/T0XX-description`.
3. Implement the task and ensure tests pass.
4. Update documentation if necessary.
5. Submit a PR with a clear description of changes.

## Testing Requirements
- New features must include unit tests.
- Integration tests must pass for the full pipeline.
- No synthetic data fabrication in tests or production code.

## Reporting Issues
Use the GitHub Issues tracker. Include:
- Python version
- Error traceback
- Steps to reproduce

## License
By contributing, you agree that your contributions will be licensed under the project's license.
