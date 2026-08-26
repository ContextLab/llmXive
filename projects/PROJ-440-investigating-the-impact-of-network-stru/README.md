# llmXive Research Pipeline: Network Structure & Energy Dissipation

## Pre-commit Hooks Setup

This project uses `pre-commit` to enforce code quality (linting with Ruff and formatting with Black) before every commit.

### Installation

1. Ensure `pre-commit` is installed:
 ```bash
 pip install pre-commit
 ```

2. Install the git hook scripts:
 ```bash
 pre-commit install
 ```

3. (Optional) Run on all existing files:
 ```bash
 pre-commit run --all-files
 ```

### Configuration

- **Black**: Enforces consistent code formatting.
- **Ruff**: Fast linting for code quality and style.
- **Codespell**: Checks for common spelling mistakes.

Configuration is defined in `.pre-commit-config.yaml`, `ruff.toml`, and `pyproject.toml` (if needed).

### Usage

When you run `git commit`, the hooks will automatically run. If any issues are found (e.g., formatting errors or linting warnings), the commit will be blocked until you fix them.

To manually run checks:
```bash
pre-commit run --all-files
```