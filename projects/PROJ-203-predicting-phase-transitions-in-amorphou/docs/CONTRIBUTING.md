# Contributing to Phase Transitions Research Pipeline

Thank you for your interest in contributing to this research project! This document outlines the guidelines for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Issues

- Use the issue tracker to report bugs or suggest features.
- Include details about your environment (OS, Python version, dependencies).
- Provide a minimal reproducible example if possible.

### Submitting Changes

1. **Fork the repository** and create a branch for your feature or bugfix.
2. **Follow the coding style**:
 - Use `black` for formatting and `isort` for imports (configured in `pyproject.toml`).
 - Add type hints where appropriate.
3. **Write tests**: Ensure your changes are covered by unit tests in `tests/`.
4. **Update documentation**: If you add a new feature, update `docs/` accordingly.
5. **Commit messages**: Use clear, descriptive commit messages.
6. **Pull Request**: Submit a PR with a detailed description of your changes.

## Development Workflow

### Setting Up the Environment

```bash
git clone <repo-url>
cd <project-root>
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
pip install -r code/requirements-dev.txt # If available
```

### Running Tests

```bash
cd code
pytest../tests/
```

### Linting and Formatting

```bash
ruff check code/
black code/
isort code/
```

## Project Guidelines

- **Task-Driven Development**: Follow the `tasks.md` list for implementation priorities.
- **Data Integrity**: Never fabricate data. All loaders must fail loudly if real data is missing.
- **Modularity**: Keep functions small and focused. Reuse existing utilities from `code/utils/`.
- **Documentation**: Update `docs/` when adding new features or changing behavior.

## Code Review

All contributions must be reviewed by at least one maintainer before merging.

## Questions?

Reach out to the maintainers if you have questions about contributing.