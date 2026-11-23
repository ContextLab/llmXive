# Linting and Formatting Configuration

This document describes the linting and formatting tools configured for the
`llmXive-the-impact-of-network-efficiency-on-age-` project.

## Tools Used

- **Ruff**: A fast Python linter (replacement for Flake8, isort, etc.)
- **Black**: The uncompromising Python code formatter

## Configuration Files

### `.ruff.toml`
Defines linting rules, line length (100 chars), and target version (Python 3.11).
- Selects common error codes: E, W, F, I, C, B, UP, N, SIM, ARG, PTH.
- Ignores `E501` (line length) as Black handles formatting.
- Configures `isort` for consistent import sorting.

### `pyproject.toml`
Contains project metadata and Black configuration.
- `[tool.black]`: Sets line length to 100 and target version.
- `[tool.ruff]`: Duplicates Ruff config for IDE compatibility.

### `.flake8`
Fallback configuration for tools that still rely on `flake8`.
- Mirrors Ruff/Black settings where possible.

## Usage

### Running via CLI
Use the provided script `code/tools/lint_format.py`:

```bash
# Check and fix linting, then format code
python code/tools/lint_format.py --fix

# Check only (no modifications)
python code/tools/lint_format.py --check-only
```

### Direct Tool Usage
```bash
# Lint with Ruff
ruff check code/

# Format with Black
black code/

# Check format without modifying
black --check code/
```

## Integration with CI

The GitHub Actions workflow (`.github/workflows/ci.yml`) automatically runs:
1. `ruff check` to ensure code adheres to style guidelines.
2. `black --check` to verify formatting.

Builds will fail if linting or formatting checks do not pass.

## Customization

- To add new linting rules, update `select` in `.ruff.toml`.
- To change line length, modify `line-length` in both `.ruff.toml` and `pyproject.toml`.
- Per-file ignores can be added in `.ruff.toml` under `[lint.per-file-ignores]`.
