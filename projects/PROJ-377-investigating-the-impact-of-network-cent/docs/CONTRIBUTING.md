# Contributing to llmXive

Thank you for your interest in contributing to this project! This document outlines the guidelines for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions.

## How to Contribute

### 1. Fork and Clone

```bash
git clone <your-fork-url>
cd PROJ-377-investigating-the-impact-of-network-cent
```

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes

- Follow the existing code style (black/flake8).
- Add tests for new features.
- Update documentation if necessary.

### 4. Run Tests

```bash
pytest tests/
```

Ensure all tests pass before committing.

### 5. Commit and Push

```bash
git add.
git commit -m "Add: descriptive message"
git push origin feature/your-feature-name
```

### 6. Submit a Pull Request

Open a PR against the `main` branch. Provide a clear description of the changes and link any relevant issues.

## Development Guidelines

### Code Style

- Use `black` for formatting.
- Use `flake8` for linting.
- Type hints are encouraged.

### Testing

- Write unit tests for new functions.
- Ensure integration tests pass.
- Aim for high test coverage.

### Documentation

- Update `README.md` and relevant `docs/` files.
- Add docstrings to all functions and classes.

### Data Handling

- Never commit raw data to the repository.
- Use `.gitignore` to exclude large files.
- Document data sources and processing steps.

## Reporting Issues

Use the issue tracker to report bugs or suggest features. Provide:
- A clear description.
- Steps to reproduce (for bugs).
- Expected vs. actual behavior.
- Environment details (OS, Python version).

## Questions?

Reach out to the maintainers via the issue tracker or email.
