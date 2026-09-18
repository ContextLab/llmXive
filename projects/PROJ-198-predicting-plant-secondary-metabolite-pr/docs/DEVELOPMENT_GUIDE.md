# Development Guide

## Getting Started

### Setup

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Configure environment variables (see `code/config_env.py`)

### Code Quality Tools

The project uses:
- **Black**: Code formatting
- **Ruff**: Linting
- **Pytest**: Testing

Configuration files:
- `.black.toml`
- `.ruff.toml`
- `pyproject.toml`

## Adding New Features

### 1. Define the Task

Add a new task to `tasks.md` with:
- Unique ID
- User story association
- Clear description
- File paths

### 2. Implement the Feature

- Follow existing patterns in the codebase
- Use Pydantic models for data validation
- Add logging at appropriate points
- Handle errors gracefully

### 3. Write Tests

- Unit tests for new functions
- Integration tests for end-to-end flows
- Edge case coverage

### 4. Update Documentation

- Update `README.md` if CLI changes
- Add/update docs in `docs/`
- Update API documentation if needed

## Code Style Guidelines

- **Naming**: Use snake_case for functions and variables
- **Docstrings**: Google-style docstrings for all public functions
- **Type Hints**: Use type hints for function signatures
- **Imports**: Group imports (standard library, third-party, local)
- **Line Length**: Max 88 characters (enforced by Black)

## Refactoring (T036)

The `code/scripts/cleanup_refactor.py` script automates:
- Unused import removal
- Function name normalization
- Docstring standardization
- Running ruff and black

Run it with:
```bash
python -m code.scripts.cleanup_refactor --project-root. --verbose
```

## Testing Strategy

- Run tests before committing: `pytest tests/`
- Aim for high coverage on critical paths
- Mock external dependencies in unit tests
- Use real data in integration tests where possible

## Continuous Integration

CI workflows should:
- Run linting and formatting checks
- Execute the full test suite
- Validate the quickstart process
- Generate coverage reports

See `.github/workflows/` for CI configuration.