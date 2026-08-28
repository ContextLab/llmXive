# llmXive: Sensitivity of Regression Coefficients

This project assesses the sensitivity of regression coefficients to dataset subset selection.

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Configure linting and formatting:
 - **Black**: Code formatter
 - **Ruff**: Fast Python linter and formatter

## Usage

### Formatting Code
Run the formatting script to apply Black and Ruff fixes:
```bash
bash scripts/format.sh
```

### Linting Code
Run the linter to check for issues without fixing them:
```bash
bash scripts/lint.sh
```

### Manual Commands
If you prefer running tools directly:
```bash
black src/ tests/
ruff check src/ tests/
```

## Project Structure
- `src/`: Source code
- `tests/`: Test suites
- `data/`: Data files (gitignored)
- `artifacts/`: Generated outputs (gitignored)
- `specs/`: Feature specifications

## Configuration
Linting and formatting rules are defined in `pyproject.toml`.
- **Line Length**: 88 characters
- **Target Version**: Python 3.9+
- **Enabled Checks**: E (Error), F (Pyflakes), I (Isort), UP (Upgrade), W (Warning)