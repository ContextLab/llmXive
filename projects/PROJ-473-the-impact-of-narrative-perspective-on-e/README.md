# llmXive: The Impact of Narrative Perspective on Empathy and Moral Judgement

## Setup Linting and Formatting

This project uses `black` for code formatting, `flake8` for linting, and `isort` for import sorting.
Pre-commit hooks are configured to run these tools automatically before commits.

### Installation

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 pip install pre-commit black flake8 isort
 ```

2. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

### Manual Usage

Run formatters and linters manually:

```bash
# Format code
black code/ tests/

# Sort imports
isort code/ tests/

# Check linting
flake8 code/ tests/
```

### Configuration Files

- `.flake8`: Linting rules and exclusions
- `pyproject.toml`: Black, isort, and pytest configuration
- `.pre-commit-config.yaml`: Pre-commit hook definitions
