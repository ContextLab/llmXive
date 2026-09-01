# Glass Transition Temperature Prediction Pipeline

## Setup Linting and Formatting

This project uses `ruff` for linting and `black` for code formatting.

### Prerequisites

Ensure you are in the project virtual environment:
```bash
source.venv/bin/activate
```

### Installation

Install the development tools (already listed in `code/requirements.txt`):
```bash
pip install ruff black
```

### Running Formatters and Linters

**Format code:**
```bash
black code/ tests/
```

**Lint code:**
```bash
ruff check code/ tests/
```

**Fix linting issues automatically:**
```bash
ruff check --fix code/ tests/
```

### Configuration

- **Black**: Configured in `pyproject.toml` with line length 88.
- **Ruff**: Configured in `pyproject.toml` and `code/ruff.toml`.
- **Pre-commit**: Optional setup via `code/.pre-commit-config.yaml`.

To install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```