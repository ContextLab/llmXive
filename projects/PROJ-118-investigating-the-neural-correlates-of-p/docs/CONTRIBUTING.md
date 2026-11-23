# Contributing to PROJ-118

Thank you for your interest in contributing to this research pipeline!

## How to Contribute

1. **Fork the repository**.
2. **Create a feature branch** based on the `main` branch.
3. **Implement your changes** following the coding standards below.
4. **Write tests** for any new functionality.
5. **Submit a pull request**.

## Coding Standards

- **Language**: Python 3.11+
- **Formatting**: Use `black` for code formatting and `flake8` for linting.
- **Imports**: Import only from the defined API surface in `code/` modules.
- **Documentation**: All public functions must have docstrings.

## Testing

- Run unit tests: `pytest tests/unit/ -v`
- Run integration tests: `pytest tests/integration/ -v`
- Ensure all tests pass before submitting a PR.

## Data Integrity

- **Never fabricate data**. All analysis must run on real data from OpenNeuro.
- If a data source is unavailable, the code should fail loudly with a clear error message.

## Code Review

- PRs must be reviewed by at least one maintainer.
- Ensure the PR description explains the changes and their impact.

## License

By contributing, you agree that your contributions will be licensed under the project's license.