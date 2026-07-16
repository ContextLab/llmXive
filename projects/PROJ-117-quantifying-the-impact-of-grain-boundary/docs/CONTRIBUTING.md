# Contributing Guide

## How to Contribute

### Reporting Issues
- Use GitHub Issues for bug reports and feature requests
- Include reproduction steps and error messages
- Specify your environment (Python version, OS, dependencies)

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
 ```bash
 git checkout -b feature/your-feature-name
 ```
3. **Make changes**
4. **Run tests**
 ```bash
 pytest tests/unit/ -v
 pytest tests/integration/ -v
 ```
5. **Run linting**
 ```bash
 ruff check code/
 black --check code/
 ```
6. **Submit a pull request**

### Code Style

- **Formatting**: Black
- **Linting**: Ruff
- **Type hints**: Use type annotations where possible
- **Documentation**: Docstrings for all public functions

### Commit Messages

Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Maintenance tasks

Example:
```
feat: add SHAP sensitivity analysis
fix: correct Miller indices calculation
docs: update API reference
```

### Testing Requirements

- All new features must include unit tests
- Integration tests must pass before merging
- Code coverage should not decrease

### Documentation Requirements

- Update `README.md` for user-facing changes
- Update `docs/api_reference.md` for API changes
- Update `docs/data_schema.md` for data format changes

### Pull Request Process

1. Ensure all tests pass
2. Update documentation as needed
3. Request review from maintainers
4. Address feedback
5. Merge after approval

## Project Structure

See `docs/architecture.md` for detailed architecture overview.

## Getting Help

- Check existing issues and documentation
- Ask questions in GitHub Discussions
- Contact maintainers via email (see repository README)
