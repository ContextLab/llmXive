# Contributing Guide

## Development Setup

### Prerequisites
- Python 3.10+
- git
- pip

### Installation
1. Clone the repository
2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
4. Configure pre-commit hooks (optional):
 ```bash
 pre-commit install
 ```

## Code Style
- **Formatting**: Black with line length 88
- **Linting**: Ruff
- **Type hints**: Use type hints for function signatures
- **Docstrings**: Google-style docstrings

### Running Formatters and Linters
```bash
# Format code
black code/ tests/

# Run linter
ruff check code/ tests/

# Fix linting issues (if possible)
ruff check --fix code/ tests/
```

## Testing
Run the test suite:
```bash
pytest tests/ -v --cov=code
```

### Writing Tests
- Place tests in `tests/` directory
- Use descriptive test names: `test_<function>_<scenario>`
- Test both normal cases and edge cases
- Mock external dependencies (UK Biobank API)

## Adding New Features
1. Create a feature branch:
 ```bash
 git checkout -b feature/description
 ```
2. Implement changes
3. Write tests
4. Run tests and linters
5. Submit a pull request

## Pull Request Process
1. Ensure all tests pass
2. Update documentation if needed
3. Add changelog entry if applicable
4. Request review from maintainers

## Git Workflow
- Use descriptive commit messages
- One logical change per commit
- Rebase on main before merging
- Squash commits if appropriate

## Documentation
- Update `docs/` when adding new features
- Keep `quickstart.md` current
- Add examples for new functionality

## Code Review
- Be respectful and constructive
- Focus on code quality and correctness
- Explain the reasoning behind suggestions
