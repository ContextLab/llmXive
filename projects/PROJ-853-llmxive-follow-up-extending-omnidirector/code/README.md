# llmXive: OmniDirector Extension

## Development Setup

1. Install dependencies:
 ```bash
 pip install -r requirements-dev.txt
 ```

2. Configure your environment (optional):
 ```bash
 # Set up pre-commit hooks if desired
 pip install pre-commit
 pre-commit install
 ```

## Usage

- **Lint**: Check code quality
 ```bash
 make lint
 ```
- **Format**: Auto-format code
 ```bash
 make format
 ```
- **Test**: Run test suite
 ```bash
 make test
 ```

## Configuration

This project uses:
- **Black** for code formatting (line length 88)
- **Ruff** for linting (replaces flake8/isort)
- **Pytest** for testing

Configuration files:
- `pyproject.toml`: Project metadata and tool configs
- `.ruff.toml`: Ruff specific settings