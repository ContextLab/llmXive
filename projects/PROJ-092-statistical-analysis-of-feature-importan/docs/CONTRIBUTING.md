# Contributing Guide

Thank you for your interest in contributing to the Feature Importance Drift Analysis Pipeline! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the project's goals

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone
cd PROJ-092-statistical-analysis-of-feature-importan
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies and dev tools
pip install -r code/requirements.txt

# Install pre-commit hooks (optional)
pre-commit install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

## Development Workflow

### Coding Standards

- **Python Style**: Follow PEP 8
- **Formatting**: Use Black for code formatting
- **Imports**: Use isort to organize imports
- **Type Hints**: Add type hints where appropriate
- **Documentation**: Include docstrings for all public functions

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=code --cov-report=html

# Run specific test file
pytest tests/test_preprocess.py
```

### Code Quality

```bash
# Run linter
flake8 code/

# Run formatter
black code/

# Sort imports
isort code/
```

### Commit Messages

Follow conventional commits:

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
style: Format code
refactor: Refactor code
test: Add tests
chore: Update build process
```

## Pull Request Process

1. **Update Documentation**: Ensure README and relevant docs are updated
2. **Add Tests**: Include tests for new functionality
3. **Verify CI**: Ensure all CI checks pass
4. **Request Review**: Assign reviewers and request feedback
5. **Address Feedback**: Make requested changes and update PR

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Commit messages follow conventions

## Reporting Issues

### Bug Reports

Include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS)
- Error messages and stack traces

### Feature Requests

Include:
- Description of the feature
- Use case and motivation
- Proposed implementation approach (if known)
- Alternative solutions considered

## Project Structure

```
PROJ-092-statistical-analysis-of-feature-importan/
├── code/ # Source code
├── data/ # Data directories
├── outputs/ # Generated outputs
├── docs/ # Documentation
├── tests/ # Test suite
└── tasks.md # Task tracking
```

## Adding New Features

### 1. Review Tasks

Check `tasks.md` for existing tasks or create a new one.

### 2. Implement

- Follow the existing module structure
- Add unit tests for new functionality
- Update API documentation

### 3. Test End-to-End

```bash
python code/main.py
python code/drift_analysis.py
python code/significance_test.py
```

### 4. Verify Outputs

Ensure all expected output files are generated correctly.

## Documentation

### Updating Docs

- Update `README.md` for user-facing changes
- Add/modify examples in `docs/QUICKSTART.md`
- Update API docs in `docs/API_REFERENCE.md`
- Add architecture diagrams if needed

### Writing Docstrings

```python
def my_function(param1: int, param2: str) -> bool:
 """
 Brief description of the function.

 Args:
 param1: Description of param1
 param2: Description of param2

 Returns:
 Description of return value

 Raises:
 ValueError: When parameter is invalid
 """
 pass
```

## Release Process

Releases are managed by maintainers. Contributors should not create releases.

## Questions?

If you have questions, please:
- Check existing issues and documentation
- Open a new issue for discussion
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the project's license.
