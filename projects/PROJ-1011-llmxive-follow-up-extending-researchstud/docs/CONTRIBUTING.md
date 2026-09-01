# Contributing to llmXive

Thank you for your interest in contributing to the llmXive automated science pipeline. This document outlines the guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive.
- Focus on constructive feedback.
- Adhere to the project's ethical guidelines regarding data usage and AI research.

## Development Workflow

1. **Fork the Repository**: Create a personal fork of the project.
2. **Create a Branch**: Create a branch for your feature or bug fix (e.g., `feature/new-analysis`).
3. **Implement Changes**: Follow the project's coding standards.
4. **Write Tests**: Ensure all new features have corresponding unit tests.
5. **Run Tests**: Verify that all tests pass locally.
6. **Submit a Pull Request**: Open a PR against the `main` branch.

## Coding Standards

- **Python Version**: Target Python 3.11+.
- **Formatting**: Use `black` for code formatting.
- **Linting**: Use `ruff` for linting.
- **Type Hinting**: Use type hints for all function arguments and return values.
- **Documentation**: Include docstrings for all public functions and classes.

## Testing Guidelines

- **Unit Tests**: Located in `tests/unit/`.
- **Integration Tests**: Located in `tests/integration/`.
- **Coverage**: Aim for high test coverage, especially for critical paths like data acquisition and statistical analysis.

## Data Handling

- **Real Data Only**: Never fabricate data. If a data source is unavailable, the pipeline must fail loudly.
- **Privacy**: Ensure no PII is included in logs or output files.
- **Licensing**: Respect the licensing terms of all external datasets.

## Documentation

- **README.md**: Keep the main README up to date with installation and usage instructions.
- **API.md**: Document all public interfaces and changes to the API.
- **CHANGELOG.md**: Maintain a changelog for version tracking.

## Review Process

- All PRs require at least one approval from a maintainer.
- CI checks must pass before merging.
- Maintain a clean commit history.

## Contact

For questions or discussions, please open an issue on the repository.
