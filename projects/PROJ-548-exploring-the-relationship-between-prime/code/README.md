# Prime Gap Analysis Project

## Linting and Formatting Configuration

This project uses **Black** for code formatting and **Ruff** for linting.

### Installation

Ensure dependencies are installed:
```bash
pip install -r requirements.txt
```

### Running Formatters/Linters Manually

**Format code with Black:**
```bash
black code/src/ code/tests/
```

**Lint code with Ruff:**
```bash
ruff check code/src/ code/tests/
ruff check --fix code/src/ code/tests/
```

### Pre-commit Hooks (Optional)

To automatically format and lint on commit:
1. Install pre-commit: `pip install pre-commit`
2. Install hooks: `pre-commit install`
3. Run manually: `pre-commit run --all-files`

The configuration is defined in `pyproject.toml` and `.pre-commit-config.yaml`.