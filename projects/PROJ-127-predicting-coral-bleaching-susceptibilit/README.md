# Coral Bleaching Susceptibility Prediction

## Setup Linting and Formatting

This project uses **Ruff** for linting and **Black** for code formatting.

### Installation

1. Install development dependencies:
 ```bash
 pip install -e ".[dev]"
 ```

### Usage

**Format code:**
```bash
black code/ tests/
```

**Lint code:**
```bash
ruff check code/ tests/
```

**Format and fix automatically:**
```bash
ruff check --fix code/ tests/
black code/ tests/
```

### Configuration

- **Ruff**: Configured in `code/ruff.toml` and `pyproject.toml`
- **Black**: Configured in `pyproject.toml`
- Target Python version: 3.11
- Line length: 88 characters
