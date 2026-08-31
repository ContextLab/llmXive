# Contributing to 316L Porosity Prediction Pipeline

Thank you for your interest in contributing to this project! This document outlines the guidelines for contributing.

## Code Style

- **Formatting**: We use `black` with a line length of 100.
- **Linting**: We use `ruff` for linting.
- **Type Hints**: Please use type hints for function arguments and return values where possible.

## Running Tests

Before submitting a pull request, ensure all tests pass:

```bash
pytest tests/ -v
```

## Project Structure

- `code/`: Contains all implementation scripts.
- `data/`: Contains raw and processed data (do not commit large data files).
- `models/`: Contains trained model artifacts.
- `results/`: Contains generated reports and plots.
- `tests/`: Contains unit and contract tests.

## Commit Messages

Please use clear and descriptive commit messages. Follow the format:

```
[TASK-ID] Short description of changes

Longer description if necessary.
```

## Reporting Issues

If you find a bug or have a feature request, please open an issue with the appropriate label.

## License

By contributing, you agree that your contributions will be licensed under the project's license.