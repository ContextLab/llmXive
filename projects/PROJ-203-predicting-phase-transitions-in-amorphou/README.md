# PROJ-203: Predicting Phase Transitions in Amorphous Solids

## Linting and Formatting Setup (Task T002)

This project uses **ruff** for linting and **black** for code formatting.

### Installation
Ensure dependencies are installed:
```bash
pip install -r code/requirements.txt
```

### Usage
- **Check Code Style**: `make lint` (runs `ruff check`)
- **Auto-Format Code**: `make format` (runs `black` and `ruff format`)
- **Run Tests**: `pytest` (includes linting checks if tools are available)

### Configuration
- Linting rules: `code/.ruff.toml`
- Formatting rules: `code/pyproject.toml` and `code/.ruff.toml`