# Contributing to PROJ-317

Thank you for your interest in contributing to the Visual Detail and False Memory research pipeline! This document outlines the guidelines for contributing to this project.

## Code of Conduct

- Be respectful and inclusive.
- Provide constructive feedback.
- Focus on the best interests of the research.

## Getting Started

1. **Fork the repository** and clone your fork.
2. **Create a feature branch** from `main`:
 ```bash
 git checkout -b feature/your-feature-name
 ```
3. **Make your changes** and commit them with clear, descriptive messages.
4. **Push your branch** to your fork:
 ```bash
 git push origin feature/your-feature-name
 ```
5. **Open a Pull Request** (PR) against the `main` branch.

## Development Guidelines

### Code Style

- **Formatting**: Use `black` for Python code formatting.
- **Linting**: Use `ruff` for linting.
- **Type Hints**: Use type hints for all function arguments and return values.
- **Docstrings**: Follow the Google or NumPy docstring style for all public functions and classes.

### Testing

- **Unit Tests**: Write unit tests for new features in `tests/unit/`.
- **Integration Tests**: Add integration tests for full pipeline workflows in `tests/integration/`.
- **Run Tests**: Ensure all tests pass before submitting a PR:
 ```bash
 pytest tests/
 ```

### Documentation

- Update the `README.md` and relevant documentation files (e.g., `docs/`) if you add new features.
- Include examples in your docstrings.

### Commits

- Use clear, imperative commit messages (e.g., "Add power analysis function").
- Reference issue numbers if applicable (e.g., "Fix #123").

## Pull Request Process

1. **Title**: Use a descriptive title (e.g., "feat: add new visualization method").
2. **Description**: Provide a clear description of the changes and the problem they solve.
3. **Review**: Wait for code review from maintainers.
4. **Changes**: Address any feedback by updating your branch and pushing new commits.
5. **Merge**: Once approved, the PR will be merged by a maintainer.

## Reporting Issues

- Use the **Issue Tracker** to report bugs or request features.
- Include:
 - A clear title and description.
 - Steps to reproduce the bug.
 - Expected vs. actual behavior.
 - Environment details (OS, Python version, etc.).

## Ethics and Compliance

- Do not include any personally identifiable information (PII) in code or data.
- Follow the [Ethics Guidelines](ethics/ethics_guidelines.md) for any data-related changes.
- Ensure all data handling complies with GDPR and institutional policies.

## Questions?

If you have questions, please open an issue or contact the maintainers.

Thank you for contributing to this research!