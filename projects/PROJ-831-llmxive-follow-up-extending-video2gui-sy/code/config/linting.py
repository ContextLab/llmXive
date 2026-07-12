"""
Linting and formatting configuration for the llmXive project.

This module provides functions to generate configuration files for
Ruff (linting) and Black (formatting) tools.
"""
import os
import yaml
from pathlib import Path

def get_project_root() -> Path:
    """Return the project root directory (parent of code/)."""
    return Path(__file__).resolve().parent.parent

def create_ruff_config() -> str:
    """
    Generate Ruff configuration (ruff.toml) content.
    
    Returns:
        str: The complete content for ruff.toml
    """
    config = """[lint]
# Enable specific rules
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
    "RUF", # Ruff-specific rules
]

# Ignore specific rules that conflict with project style
ignore = [
    "E501", # Line too long (handled by Black)
    "B008", # Do not perform function call in argument defaults (common in Pydantic)
]

# Allow autofix for all enabled rules
fixable = ["ALL"]
unfixable = []

# Exclude standard directories
exclude = [
    ".git",
    ".tox",
    ".eggs",
    "node_modules",
    "venv",
    ".venv",
    "build",
    "dist",
    "__pycache__",
]

# Per-file ignores
[lint.per-file-ignores]
"__init__.py" = ["F401"]  # Ignore unused imports in __init__.py

[lint.isort]
known-first-party = ["code"]
force-single-line = false
lines-between-types = 0
lines-after-imports = 2

[format]
# Use double quotes for strings
quote-style = "double"
# Indent with spaces
indent-style = "space"
# Skip magic trailing comma
skip-magic-trailing-comma = false
# Line length (Black default)
line-length = 88
"""
    return config

def create_black_config() -> str:
    """
    Generate Black configuration (pyproject.toml section) content.
    
    Returns:
        str: The Black configuration section for pyproject.toml
    """
    config = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    \.git
    | \.tox
    | \.eggs
    | node_modules
    | venv
    | \.venv
    | build
    | dist
    | __pycache__
)/
'''
"""
    return config

def create_precommit_config() -> str:
    """
    Generate .pre-commit-config.yaml content.
    
    Returns:
        str: The complete content for .pre-commit-config.yaml
    """
    config = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
- id: trailing-whitespace
- id: end-of-file-fixer
- id: check-yaml
- id: check-added-large-files
- id: detect-private-key

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.6
    hooks:
- id: ruff
  args: [--fix, --exit-non-zero-on-fix]
- id: ruff-format

  - repo: https://github.com/psf/black-pre-commit-mirror
    rev: 23.11.0
    hooks:
- id: black
  language_version: python3.11
"""
    return config

def write_linting_configs():
    """
    Write all linting and formatting configuration files to the project root.
    
    Creates:
        - ruff.toml
        - .pre-commit-config.yaml
        - Updates pyproject.toml with Black config
    """
    root = get_project_root()
    
    # Write ruff.toml
    ruff_path = root / "ruff.toml"
    ruff_path.write_text(create_ruff_config())
    print(f"Created: {ruff_path}")
    
    # Write .pre-commit-config.yaml
    precommit_path = root / ".pre-commit-config.yaml"
    precommit_path.write_text(create_precommit_config())
    print(f"Created: {precommit_path}")
    
    # Append Black config to pyproject.toml
    pyproject_path = root / "pyproject.toml"
    if pyproject_path.exists():
        existing = pyproject_path.read_text()
        if "[tool.black]" not in existing:
            pyproject_path.write_text(existing + "\n" + create_black_config())
            print(f"Updated: {pyproject_path} (added Black config)")
        else:
            print(f"Skipped: {pyproject_path} (Black config already present)")
    else:
        pyproject_path.write_text(create_black_config())
        print(f"Created: {pyproject_path} (with Black config)")

if __name__ == "__main__":
    write_linting_configs()