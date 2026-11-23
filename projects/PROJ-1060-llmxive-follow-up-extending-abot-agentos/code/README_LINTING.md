# Linting and Formatting Configuration

This project uses **Black** for code formatting and **Ruff** for linting.

## Configuration Files

- `pyproject.toml`: Contains configuration for both Black and Ruff, as well as pytest.
- `.ruff.toml`: Explicit Ruff configuration (mirrored in pyproject.toml for consistency).

## Tools

- **Black**: Enforces a consistent code style.
- **Ruff**: A fast Python linter and formatter (alternative to Flake8, isort, etc.).

## Usage

### Running Formatters and Linters

Ensure you have the dependencies installed:
```bash
pip install -r code/requirements.txt
```

**Format Code:**
```bash
black code/
```

**Lint Code:**
```bash
ruff check code/
```

**Fix Issues:**
```bash
ruff check code/ --fix
black code/
```

### Using Helper Scripts

The project includes helper scripts in `code/scripts/`:

- `format.sh`: Runs Black and checks Ruff.
- `lint.sh`: Runs Ruff check.
- `format_fix.sh`: Automatically fixes issues where possible.

Example:
```bash
cd code
./scripts/format_fix.sh
```

## Pre-commit Hooks (Optional)

To run these checks automatically before committing, you can set up `pre-commit`:

1. Install pre-commit: `pip install pre-commit`
2. Create `.pre-commit-config.yaml` in the project root:
 ```yaml
 repos:
 - repo: https://github.com/psf/black
 rev: 23.12.1
 hooks:
 - id: black
 args: ["--line-length", "120"]
 - repo: https://github.com/astral-sh/ruff-pre-commit
 rev: v0.1.11
 hooks:
 - id: ruff
 args: ["--fix", "--exit-non-zero-on-fix"]
 ```
3. Install hooks: `pre-commit install`

## Configuration Details

- **Line Length**: 120 characters.
- **Target Version**: Python 3.10.
- **Linter Rules**: E, F, W, I, N, UP, B, C4, SIM.
- **Isort**: Configured to recognize project modules as first-party.