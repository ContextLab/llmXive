# Contributing Guide

## Code Style
- **Formatting**: Use Black for Python code formatting
- **Linting**: Use Ruff for code quality checks
- **Type Hints**: Prefer type hints for all function signatures
- **Docstrings**: Use Google-style docstrings for all public functions

## Development Workflow

1. **Create a feature branch**
```bash
git checkout -b feature/description
```

2. **Make changes**
- Implement the feature or fix
- Write/update tests
- Update documentation if needed

3. **Run tests**
```bash
pytest tests/
```

4. **Check code quality**
```bash
ruff check code/
black --check code/
```

5. **Commit changes**
```bash
git add.
git commit -m "feat: description of changes"
```

6. **Push and create pull request**
```bash
git push origin feature/description
```

## Testing Guidelines

- **Unit Tests**: Test individual functions in `tests/unit/`
- **Integration Tests**: Test component interactions in `tests/integration/`
- **Contract Tests**: Verify API contracts in `tests/contract/`
- **Test Coverage**: Aim for >80% code coverage

## Documentation Standards

- Update `docs/` when adding new features
- Include examples in docstrings
- Keep `README.md` and `quickstart.md` up to date
- Document breaking changes in `CHANGELOG.md`

## Ethics Compliance

- Never store PII in logs or test data
- Use anonymized data in examples
- Follow GDPR guidelines for data handling
- Reference ethics documentation in `docs/ethics.md`

## Review Process

1. Automated checks (CI) run on PR creation
2. Peer review by at least one team member
3. Address feedback and update PR
4. Merge after approval

## Release Process

1. Version bump in `code/config.py`
2. Update `CHANGELOG.md`
3. Create git tag
4. Publish to package repository (if applicable)

## Questions?
Reach out to the project maintainers for guidance on contributing.
