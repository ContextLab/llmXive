# Narrative Archaeology: Reverse-Engineering Story Memories from Brain Data

## Project Setup

This project uses Python 3.11+ with the following linting and formatting tools:

- **black**: Code formatter
- **flake8**: Linter
- **isort**: Import sorter
- **pre-commit**: Git hooks for automated checks

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Development Workflow

### Running Linters Manually

```bash
# Check formatting
black --check code/ tests/

# Fix formatting
black code/ tests/

# Check imports
isort --check code/ tests/

# Fix imports
isort code/ tests/

# Run linter
flake8 code/ tests/
```

### Using Pre-commit

Run all checks before committing:
```bash
pre-commit run --all-files
```

## Configuration Files

- `.flake8`: Flake8 linting rules
- `pyproject.toml`: Black, isort, and pytest configuration
- `.pre-commit-config.yaml`: Pre-commit hook definitions
- `requirements.txt`: Project dependencies

## Testing

Run tests with pytest:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=code --cov-report=html
```

## Architecture

- `code/`: Source code for the research pipeline
- `data/`: Data files and outputs
- `tests/`: Test suite
- `docs/`: Documentation
- `specs/`: Feature specifications