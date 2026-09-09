# Contributing to the Visual Priming Research Project

Thank you for your interest in contributing! This document outlines the guidelines and processes for contributing to this research project.

## Code of Conduct

Please be respectful and constructive in all interactions. This project is committed to fostering an open and welcoming environment.

## Getting Started

1. **Fork the Repository**: Click the "Fork" button on the project's GitHub page.
2. **Clone Your Fork**:
 ```bash
 git clone
 cd project-name
 ```
3. **Create a Branch**:
 ```bash
 git checkout -b feature/your-feature-name
 ```

## Development Workflow

### Setting Up the Environment

Follow the steps in `quickstart.md` to set up your local environment.

### Making Changes

- Write clear, concise code.
- Add tests for new features.
- Update documentation as needed.
- Ensure all tests pass before committing.

### Commit Messages

Use descriptive commit messages that explain the purpose of the changes. Follow the format:

```
<type>: <short description>

<optional detailed description>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

### Pull Requests

1. Push your branch to your fork:
 ```bash
 git push origin feature/your-feature-name
 ```
2. Open a pull request (PR) against the `main` branch of the original repository.
3. Provide a clear description of the changes and reference any related issues.
4. Wait for review and address any feedback.

## Code Style

- Follow PEP 8 guidelines.
- Use `black` for formatting and `ruff` for linting.
- Run `pre-commit` hooks before committing:
 ```bash
 pre-commit run --all-files
 ```

## Testing

- Write unit tests for new features.
- Ensure all tests pass:
 ```bash
 pytest tests/
 ```
- Include integration tests for critical workflows.

## Documentation

- Update `README.md` and `quickstart.md` for user-facing changes.
- Add inline comments for complex logic.
- Document new functions and classes with docstrings.

## Review Process

- PRs will be reviewed by maintainers.
- Feedback will be provided promptly.
- Changes may be requested before approval.

## Release Process

- Releases are managed by maintainers.
- Versioning follows semantic versioning.
- Release notes will be published for each release.

## Questions?

If you have questions, please open an issue on the repository.

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
