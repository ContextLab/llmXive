# Linting and Formatting Configuration for llmXive

## Overview
This project uses a multi-layered approach to code quality:
1. **Ruff** (primary linter) - Fast, comprehensive rule checking
2. **Black** (formatter) - Opinionated code formatting
3. **Flake8** (compatibility layer) - Legacy support and additional checks
4. **Pre-commit hooks** - Automated checks before commits
5. **Mypy** (type checking) - Static type analysis

## Configuration Files

- `.ruff.toml` - Ruff linting rules and formatting settings
- `.flake8` - Flake8 configuration for compatibility
- `pyproject.toml` - Black settings and pytest configuration
- `.pre-commit-config.yaml` - Pre-commit hook definitions

## Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Install development dependencies
pip install -r requirements.txt
pip install ruff black flake8 mypy pre-commit
```

## Usage

### Run linter manually
```bash
ruff check code/
```

### Run formatter
```bash
black code/
# Or using ruff
ruff format code/
```

### Run all checks
```bash
pre-commit run --all-files
```

### Run tests
```bash
pytest code/tests/
```

## Rules and Conventions

- **Line length**: 88 characters (Black default)
- **Quote style**: Double quotes
- **Imports**: Sorted with isort, grouped by type
- **Type hints**: Required for function signatures
- **Print statements**: Forbidden in production code (use logging)

## CI Integration

The linting configuration is designed to work with CI pipelines:
- Failing lint checks will block merges
- Type checking is optional but recommended
- Test coverage is enforced via pytest

## Troubleshooting

If you encounter linting errors:
1. Run `ruff check --fix code/` to auto-fix issues
2. Run `black code/` to format code
3. For persistent issues, check the specific rule documentation