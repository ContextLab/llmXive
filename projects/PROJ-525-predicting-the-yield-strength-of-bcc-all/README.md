# Predicting Yield Strength of BCC Alloys

This project implements an automated scientific pipeline to predict the yield strength of Body-Centered Cubic (BCC) alloys using machine learning.

## Prerequisites

- Python 3.11+
- pip

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -e.
 pip install -e ".[dev]" # For development tools
 ```

3. Install pre-commit hooks (optional but recommended):
 ```bash
 pip install pre-commit
 pre-commit install
 ```

## Linting and Formatting

This project uses `ruff` for linting and `black` for code formatting.

### Check Mode (CI/CD)
Run the linters to check for issues without modifying files:
```bash
python -m code.lint_format check
```

### Fix Mode (Local Development)
Automatically fix formatting and linting issues:
```bash
python -m code.lint_format fix
```

Alternatively, use pre-commit hooks:
```bash
pre-commit run --all-files
```

## Project Structure

- `code/`: Source code modules
- `data/`: Data storage (raw, processed, logs)
- `tests/`: Unit and integration tests
- `reports/`: Generated reports and metrics
- `state/`: Pipeline state tracking

## License

MIT License