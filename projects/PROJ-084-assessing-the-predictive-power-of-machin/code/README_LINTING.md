# Linting and Formatting Configuration

This project uses `ruff` for linting and `black` for code formatting.

## Installation

Ensure dependencies are installed:
```bash
pip install -r code/requirements.txt
```

## Usage

### Run Linter
```bash
ruff check code/
```

### Run Linter with Auto-fix
```bash
ruff check --fix code/
```

### Run Formatter
```bash
black code/
```

### Format and Lint in one step (pre-commit style)
```bash
black code/ && ruff check --fix code/
```

## Configuration Files
- `code/.ruff.toml`: Ruff configuration
- `code/pyproject.toml`: Black and Pytest configuration