# Linting and Formatting Configuration

This project uses the following tools for code quality:

## Tools

- **Black**: Code formatter
- **flake8**: Linter
- **isort**: Import sorter
- **pre-commit**: Git hooks manager

## Installation

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Install pre-commit hooks:
 ```bash
 pre-commit install
 ```

## Usage

### Running formatters and linters manually

```bash
# Format code with Black
black code/

# Sort imports with isort
isort code/

# Run flake8
flake8 code/
```

### Running pre-commit hooks

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run hooks on staged files only (automatic on git commit)
pre-commit run
```

## Configuration Files

- `.flake8`: Flake8 configuration
- `pyproject.toml`: Black, isort, pytest, and other tool configurations
- `.pre-commit-config.yaml`: Pre-commit hooks configuration

## CI/CD Integration

These tools are typically run in CI/CD pipelines to ensure code quality before merging.
Add the following to your CI configuration:

```yaml
- name: Lint and Format
 run: |
 pre-commit run --all-files
```