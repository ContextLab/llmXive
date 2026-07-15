# Contributing to the Research Pipeline

Thank you for your interest in contributing to the Network Structure & Neural Avalanche Dynamics research pipeline! This document outlines the guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive.
- Provide constructive feedback.
- Focus on the quality of the research and code.

## How to Contribute

### 1. Fork the Repository

Create a fork of the repository on GitHub.

### 2. Create a Branch

Create a new branch for your feature or bug fix:

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes

- Follow the existing code style (black, ruff).
- Write clear, concise commit messages.
- Update documentation if necessary.

### 4. Run Tests

Ensure all tests pass before submitting:

```bash
pytest tests/
```

### 5. Submit a Pull Request

- Push your branch to your fork.
- Open a pull request against the `main` branch.
- Provide a clear description of the changes.

## Development Workflow

### Environment Setup

1. Create a virtual environment (see `INSTALLATION.md`).
2. Install dependencies: `pip install -r code/requirements.txt`.
3. Install development tools: `pip install pre-commit`.
4. Run `pre-commit install` to set up hooks.

### Coding Standards

- **Style**: Use `black` for formatting and `ruff` for linting.
- **Type Hints**: Use type hints for all function arguments and return values.
- **Docstrings**: Include docstrings for all public modules, functions, and classes.
- **Logging**: Use the `logger` module for logging messages.

### Testing

- Write unit tests for new features.
- Ensure tests cover edge cases.
- Aim for high test coverage.

### Documentation

- Update `docs/` files when adding new features.
- Keep the `README.md` and `API_REFERENCE.md` up to date.

## Reporting Issues

If you find a bug or have a suggestion:
1. Check existing issues on GitHub.
2. Create a new issue with a clear title and description.
3. Include steps to reproduce the bug (if applicable).

## Review Process

- Pull requests will be reviewed by maintainers.
- Feedback will be provided within a reasonable timeframe.
- Address feedback and update the PR accordingly.

## License

By contributing, you agree that your contributions will be licensed under the project's license.

## Questions?

If you have any questions, feel free to open an issue or contact the maintainers.

Thank you for contributing!
