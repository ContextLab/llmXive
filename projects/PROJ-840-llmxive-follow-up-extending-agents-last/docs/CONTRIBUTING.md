# Contributing to llmXive Automated Science Pipeline

Thank you for your interest in contributing to the llmXive Automated Science Pipeline! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- Familiarity with the project's domain (agent benchmarks, failure analysis)

### Setting Up Development Environment

1. **Fork the repository**
 ```bash
 git clone
 cd PROJ-840-llmxive-follow-up-extending-agents-last
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 ```

3. **Install dependencies**
 ```bash
 pip install -r requirements.txt
 ```

4. **Install in development mode**
 ```bash
 pip install -e.
 ```

5. **Set up pre-commit hooks** (optional but recommended)
 ```bash
 pre-commit install
 ```

## Development Workflow

### Branching Strategy

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: New features (e.g., `feature/us2-intervention`)
- `bugfix/*`: Bug fixes
- `hotfix/*`: Critical production fixes

### Making Changes

1. **Create a feature branch**
 ```bash
 git checkout -b feature/your-feature-name
 ```

2. **Make your changes**
 - Follow the existing code style
 - Add tests for new functionality
 - Update documentation as needed

3. **Run tests**
 ```bash
 pytest tests/
 ```

4. **Run linter and formatter**
 ```bash
 ruff check code/
 black --check code/
 ```

5. **Commit your changes**
 ```bash
 git commit -m "feat: add new feature"
 ```

### Commit Message Convention

We follow the Conventional Commits specification:

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(classification): add new normalization heuristic
fix(analysis): correct p-value calculation in McNemar's test
docs(quickstart): update installation instructions
```

## Testing Guidelines

### Writing Tests

- **Unit Tests**: Test individual functions
- **Integration Tests**: Test component interactions
- **Contract Tests**: Verify API compliance
- **Golden Set Tests**: Validate against known results

### Test Requirements

- All new code must have tests
- Tests must pass before merging
- Aim for high test coverage
- Use descriptive test names

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_heuristics.py

# Run with coverage
pytest tests/ --cov=code --cov-report=html

# Run with verbose output
pytest tests/ -v
```

## Code Style

### Formatting

We use Black for code formatting:

```bash
black code/
```

### Linting

We use Ruff for linting:

```bash
ruff check code/
```

### Type Hints

Use type hints for all function parameters and return values.

### Documentation

- Use docstrings for all public functions and classes
- Follow Google or NumPy docstring style
- Keep documentation up to date

## Pull Request Process

1. **Create a pull request**
 ```bash
 git push origin feature/your-feature-name
 ```

2. **Fill out the PR template**
 - Describe the changes
 - Link related issues
 - Include test results

3. **Address review feedback**
 - Make requested changes
 - Update tests if needed
 - Re-run all tests

4. **Merge approval**
 - At least one reviewer approval required
 - All tests must pass
 - No merge conflicts

## Documentation Contributions

### Updating Documentation

- Update `docs/quickstart.md` for user-facing changes
- Update `docs/ARCHITECTURE.md` for architectural changes
- Update `docs/CONTRIBUTING.md` for contribution process changes
- Update inline code documentation

### Documentation Standards

- Clear and concise language
- Code examples where appropriate
- Consistent formatting
- Up-to-date information

## Issue Reporting

### Bug Reports

When reporting bugs, include:

- Description of the issue
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Error messages and stack traces

### Feature Requests

When requesting features, include:

- Description of the feature
- Use case and benefits
- Proposed implementation approach (optional)

## Release Process

Releases are managed by the maintainers. Contributors should:

- Ensure their code is ready for release
- Update version numbers if applicable
- Add entries to CHANGELOG.md

## Questions?

If you have questions, please:

1. Check existing issues and documentation
2. Open a new issue for discussion
3. Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the project's license.

## Acknowledgments

Thank you to all contributors who make this project better!
