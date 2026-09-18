# Contributing Guide

## Welcome!

Thank you for your interest in contributing to the llm-code-review-impact research project. This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. This is a research project focused on scientific inquiry.

## Getting Started

### 1. Fork and Clone

```bash
git clone
cd llm-code-review-impact
```

### 2. Set Up Development Environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install Development Tools

```bash
# Ensure ruff and black are available
ruff --version
black --version
```

## Development Workflow

### Branch Naming

Use descriptive branch names:

```bash
# Feature branches
git checkout -b feature/add-new-metric

# Bug fix branches
git checkout -b fix/classification-edge-case

# Documentation branches
git checkout -b docs/update-api-reference
```

### Making Changes

1. Create a new branch from `main`
2. Make your changes
3. Write or update tests
4. Run linting and formatting
5. Run tests
6. Commit with clear messages
7. Push and create a pull request

### Code Style

We use:
- **Black** for formatting (line length: 100)
- **Ruff** for linting
- **isort** for import sorting (via ruff)

Format and lint before committing:

```bash
black code/ tests/
ruff check code/ tests/
ruff format code/ tests/
```

### Testing

Run tests before submitting:

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=code --cov-report=html
```

### Commit Messages

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add cyclomatic complexity calculation for PR diffs"
git commit -m "Fix: Handle empty PR diffs in complexity analysis"
git commit -m "Docs: Update API documentation for classify_prs module"

# Avoid
git commit -m "Fixed stuff"
git commit -m "WIP"
```

## Pull Request Process

### 1. Create a PR

- Push your branch to your fork
- Open a pull request to `main`
- Fill out the PR template

### 2. PR Checklist

Before submitting, ensure:

- [ ] Code follows style guidelines (black, ruff)
- [ ] Tests added for new functionality
- [ ] All tests pass
- [ ] Documentation updated
- [ ] No sensitive data committed
- [ ] Commit history is clean (no "WIP" commits)

### 3. Review

- Maintainers will review your PR
- Address feedback promptly
- Squash commits if requested

### 4. Merge

- PR will be merged after approval
- Branch may be deleted after merge

## Types of Contributions

### Bug Reports

If you find a bug:

1. Check existing issues
2. Create a new issue with:
 - Description of the bug
 - Steps to reproduce
 - Expected vs actual behavior
 - Environment details

### Feature Requests

For new features:

1. Check existing issues
2. Create an issue describing:
 - The problem you're solving
 - Proposed solution
 - Use cases

### Documentation

Documentation improvements are always welcome:

- Fix typos or unclear explanations
- Add examples
- Update API documentation
- Improve diagrams

### Code Contributions

We welcome:

- Bug fixes
- Performance improvements
- New metrics or analysis methods
- Test coverage improvements
- Refactoring for clarity

## Task Implementation Guidelines

### Following the Task List

This project uses a task-based workflow. When implementing a task:

1. Read the task description in `tasks.md`
2. Check dependencies and prerequisites
3. Review the API surface to use existing names
4. Implement the task completely (no stubs or TODOs)
5. Write tests if requested
6. Verify all artifacts are created

### One Task at a Time

- Implement exactly one task per PR
- Don't start multiple tasks simultaneously
- Don't "improve" unrelated files

### Artifact Requirements

- All Python files must be syntactically valid
- Scripts must produce real output files
- No synthetic/fake data allowed
- Fail loudly on errors, never silently

## Documentation Standards

### Docstrings

Use Google-style docstrings:

```python
def calculate_complexity(code: str) -> float:
 """Calculate cyclomatic complexity for given code.

 Args:
 code: Python source code as a string.

 Returns:
 Cyclomatic complexity score as a float.

 Raises:
 SyntaxError: If code contains syntax errors.
 """
 pass
```

### README Updates

When adding features:
- Update `docs/README.md`
- Add new sections as needed
- Keep examples up to date

## Review Guidelines

### For Reviewers

- Be constructive and respectful
- Focus on code quality and correctness
- Check for test coverage
- Verify documentation is updated
- Ensure no security issues

### For Contributors

- Be open to feedback
- Address comments promptly
- Ask for clarification if needed
- Don't take feedback personally

## Release Process

### Versioning

We use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

Before releasing:

- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version number bumped
- [ ] Release notes written

## Questions?

If you have questions:

1. Check existing documentation
2. Search existing issues
3. Create a new issue for discussion

## License

By contributing, you agree that your contributions will be licensed under the project's license.