# Contributing to llmXive

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Workflow

### 1. Setup

```bash
# Fork and clone
git clone
cd llmXive

# Create feature branch
git checkout -b feature/your-feature-name

# Install dependencies
pip install -r requirements.txt
```

### 2. Code Style

- **Formatting**: Black (auto-formatted)
- **Linting**: Ruff/flake8
- **Type Hints**: Required for all function signatures
- **Docstrings**: Google style for all public functions

Run formatters before committing:
```bash
black code/
ruff check code/ --fix
```

### 3. Testing

- Write tests before implementation (TDD approach)
- All tests must pass before merging
- Maintain ≥ 80% code coverage

```bash
pytest tests/ --cov=code
```

### 4. Data Hygiene

- **Never fabricate data**: Always use real sources
- **Checksums**: Record SHA-256 of all downloaded datasets
- **Reproducibility**: Set random seeds explicitly

## Pull Request Process

1. Update documentation for new features
2. Add tests for new functionality
3. Ensure all existing tests pass
4. Update `CHANGELOG.md` with changes
5. Request review from maintainers

## Code Review Guidelines

### What We Look For

- ✅ Clear, descriptive commit messages
- ✅ Comprehensive test coverage
- ✅ Proper documentation updates
- ✅ No fabrication of data or results
- ✅ Adherence to resource limits (6h/7GB)

### Common Issues

- ❌ Placeholder code or TODOs
- ❌ Synthetic data instead of real sources
- ❌ Missing type hints
- ❌ Unnecessary dependencies
- ❌ Ignoring resource constraints

## Architecture Decisions

Follow the existing architecture documented in:
- `docs/DESIGN.md`
- `docs/ARCHITECTURE.md`

When proposing changes:
1. Explain the rationale
2. Show impact on existing components
3. Provide migration path if breaking changes

## Reporting Issues

### Bug Reports

Include:
- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Full traceback

### Feature Requests

Include:
- Use case description
- Expected behavior
- Alternative solutions considered

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
