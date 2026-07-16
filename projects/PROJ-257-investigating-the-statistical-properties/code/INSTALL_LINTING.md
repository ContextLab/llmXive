# Linting and Formatting Setup

This project uses **ruff** for linting and **black** for code formatting.

## Installation

1. Ensure you are in the project root virtual environment:
 ```bash
 source venv/bin/activate
 ```
2. Install the tools (already listed in `requirements.txt`):
 ```bash
 pip install -r requirements.txt
 ```

## Usage

### Run Linter (Ruff)
```bash
ruff check code/
```

### Run Formatter (Black)
```bash
black code/
```

### Install Pre-commit Hooks
To automatically run these checks before every commit:
```bash
pre-commit install
```

### Run All Checks Manually
```bash
pre-commit run --all-files
```

## Configuration
- **Black**: Configured in `pyproject.toml` (line-length: 88, target: py311).
- **Ruff**: Configured in `.ruff.toml` (selects E, W, F, I, C, B, UP).
- **Pre-commit**: Configured in `.pre-commit-config.yaml`.