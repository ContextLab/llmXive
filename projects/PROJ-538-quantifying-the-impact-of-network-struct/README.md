# Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

## Project Setup

This project uses Python 3.11+ and relies on `ruff` for linting and `black` for formatting.

### Dependencies

Install dependencies:
```bash
pip install -r requirements.txt
```

### Code Quality Tools

#### Configuration

- **Ruff**: Configured in `pyproject.toml` under `[tool.ruff]`.
- **Black**: Configured in `pyproject.toml` under `[tool.black]`.
- **Pytest**: Configured in `pyproject.toml` under `[tool.pytest.ini_options]`.

#### Usage

**Format Code:**
```bash
./scripts/format_code.sh fix
```

**Check Formatting & Linting:**
```bash
./scripts/format_code.sh check
```

**Run Linting Only:**
```bash
./scripts/lint_check.sh
```

**Run Tests:**
```bash
pytest
```

## Project Structure

- `code/`: Source code
- `tests/`: Test suite
- `data/`: Data directory (ignored by linting)
- `figures/`: Output figures (ignored by linting)
- `scripts/`: Utility scripts for formatting and linting
- `pyproject.toml`: Project configuration including tool settings

## Development Guidelines

1. All code must be formatted with `black` before committing.
2. All code must pass `ruff` linting checks.
3. Import sorting is enforced via `ruff` (isort rules).
4. Tests must be run via `pytest` with coverage enabled.