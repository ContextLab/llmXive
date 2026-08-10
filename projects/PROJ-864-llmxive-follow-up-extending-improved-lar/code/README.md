# llmXive Follow-up: Extending Improved Large Language Diffusion Models

## Codebase Setup & Tooling

This project uses **Ruff** for linting and **Black** for formatting.

### Prerequisites
- Python 3.11+
- pip

### Installation
```bash
cd code/
pip install -r requirements.txt
```

### Formatting (Black)
Format all Python files in the project:
```bash
black.
```

### Linting (Ruff)
Check for linting errors:
```bash
ruff check.
```

To fix automatic linting issues:
```bash
ruff check --fix.
```

### Configuration
Tool configurations are defined in `pyproject.toml`:
- **Black**: Line length 100, Python 3.11 target
- **Ruff**: Comprehensive rule set (E, W, F, I, B, C4, UP) with project-specific ignores