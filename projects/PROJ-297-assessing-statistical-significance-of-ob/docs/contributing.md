# Contributing Guide

## How to Contribute

We welcome contributions to this project! Please follow these guidelines:

## Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Install dependencies: `pip install -r requirements.txt`
4. Install development tools: `pip install black flake8 pytest`

## Code Style

- **Formatting**: Use `black` with line length 88
- **Imports**: Use `isort` for import organization
- **Linting**: Run `flake8` before committing
- **Type Hints**: Add type hints to all functions

Run code style checks:
```bash
black --check code/
isort --check-only code/
flake8 code/
```

## Testing

- All new features must include tests
- Tests should be placed in `tests/unit/` or `tests/integration/`
- Run tests before submitting:
 ```bash
 pytest tests/ -v
 ```

## Commit Messages

- Use clear, descriptive commit messages
- Reference task IDs when applicable (e.g., "Fix T029: Update documentation")
- Follow the format: `[TASK-ID] Short description`

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Request review from maintainers
4. Address feedback and update PR

## Data Integrity

- **Never fabricate data**: All data must come from real sources (UCI repository)
- **No synthetic fallbacks**: If data loading fails, raise an error
- **Verify sources**: Use verified URLs and checksums

## Documentation

- Update `README.md` for user-facing changes
- Add/modify docs in `docs/` for methodology or API changes
- Include examples where helpful

## Reporting Issues

- Use the issue tracker for bugs or feature requests
- Provide reproduction steps for bugs
- Include environment information (Python version, OS)

## Code Review

- Be constructive and respectful
- Focus on code quality and correctness
- Consider performance implications

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
