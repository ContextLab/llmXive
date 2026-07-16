# Linting and Formatting Configuration

This project uses **Ruff** for linting and **Black** for code formatting to ensure consistent code style across the codebase.

## Installation

The required tools are included in `requirements.txt`:

```bash
pip install ruff black
```

## Configuration

### Ruff

Ruff configuration is defined in:
- `code/config/linting.py` (programmatic configuration)
- `code/config/linting_config.toml` (TOML configuration file)

Key settings:
- Target Python version: 3.11
- Line length: 88 characters
- Selected rules: E, W, F, I, B, C4, UP, ARG, SIM
- Ignored rules: E501 (line length handled by Black), B008, ARG001

### Black

Black configuration is defined in:
- `code/config/linting.py` (programmatic configuration)
- `code/config/linting_config.toml` (TOML configuration file)

Key settings:
- Line length: 88 characters
- Target Python version: 3.11
- String normalization: enabled

## Usage

### Run Ruff Linting

```bash
# Check for issues without fixing
ruff check code/

# Automatically fix issues
ruff check --fix code/

# Check specific file
ruff check code/data/features.py
```

### Run Black Formatting

```bash
# Format all Python files
black code/

# Check formatting without making changes
black --check code/

# Format specific file
black code/data/features.py
```

### Run Validation Script

```bash
# Validate linting setup
python code/config/linting.py
```

## Pre-commit Hooks (Optional)

To run linting and formatting automatically before commits, you can set up pre-commit hooks:

1. Install pre-commit:
 ```bash
 pip install pre-commit
 ```

2. Create `.pre-commit-config.yaml`:
 ```yaml
 repos:
 - repo: https://github.com/astral-sh/ruff-pre-commit
 rev: v0.1.0
 hooks:
 - id: ruff
 args: [--fix]
 - id: ruff-format

 - repo: https://github.com/psf/black
 rev: 23.0.0
 hooks:
 - id: black
 ```

3. Install the hooks:
 ```bash
 pre-commit install
 ```

## CI Integration

The linting configuration is designed to work with GitHub Actions CI. Add the following to your workflow:

```yaml
- name: Lint with Ruff
 run: |
 pip install ruff
 ruff check code/

- name: Check formatting with Black
 run: |
 pip install black
 black --check code/
```

## Customization

To customize the linting rules:

1. Edit `code/config/linting_config.toml` for TOML-based configuration
2. Update `get_ruff_config()` and `get_black_config()` in `code/config/linting.py` for programmatic configuration
3. Run `python code/config/linting.py` to validate changes

## Troubleshooting

### "Module not found" errors

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Configuration not being picked up

Make sure `pyproject.toml` or `.ruff.toml` is in the project root, or run ruff with explicit config path:
```bash
ruff check --config code/config/linting_config.toml code/
```

### Conflicting rules

If you encounter conflicting rules, adjust the `ignore` list in `get_ruff_config()` or `linting_config.toml`.