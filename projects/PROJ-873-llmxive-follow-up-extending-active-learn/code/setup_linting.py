"""
Setup script for linting and formatting tools (ruff, black).
This script ensures configuration files exist and provides a quickstart
for running linters/formatters.
"""
import os
import sys
from typing import List, Tuple

def ensure_config_files() -> List[str]:
    """
    Creates or updates configuration files for ruff and black.
    Returns a list of created/updated file paths.
    """
    created_files = []

    # 1. Create .ruff.toml
    ruff_config_path = ".ruff.toml"
    if not os.path.exists(ruff_config_path):
        ruff_content = """# Ruff configuration for llmXive project

# Target Python version
target-version = "py311"

# Line length (Black default)
line-length = 88

[lint]
# Enable Pyflakes, pycodestyle, isort, and flake8
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
    "N",  # pep8-naming
    "RUF",# Ruff-specific rules
]

# Ignore specific rules if necessary
ignore = [
    "E501", # Line too long (handled by Black)
    "B008", # Do not perform function call in argument defaults (common in dataclasses)
    "RUF012", # Mutable class attributes should be annotated with `typing.ClassVar`
]

# Per-file ignores (optional)
# [lint.per-file-ignores]
# "tests/*" = ["S101"] # Allow assert in tests

[lint.isort]
known-first-party = ["config", "data_loader", "env_validator", "logging_config", "metrics", "models", "run_baseline_unique", "sampling", "setup_linting", "unique_subset_generator", "utils"]
force-single-line = true
lines-after-imports = 2

[format]
# Black-compatible formatting
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
        with open(ruff_config_path, "w", encoding="utf-8") as f:
            f.write(ruff_content)
        created_files.append(ruff_config_path)
        print(f"Created {ruff_config_path}")
    else:
        print(f"Skipped {ruff_config_path} (already exists)")

    # 2. Create pyproject.toml with Black settings (if not exists)
    pyproject_path = "pyproject.toml"
    if not os.path.exists(pyproject_path):
        pyproject_content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive"
version = "0.1.0"
description = "Active Learners as Efficient PRP Rerankers"
requires-python = ">=3.11"

[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.mypy_cache
  | \\.venv
  | build
  | dist
)/
'''

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
"""
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(pyproject_content)
        created_files.append(pyproject_path)
        print(f"Created {pyproject_path}")
    else:
        print(f"Skipped {pyproject_path} (already exists)")

    return created_files


def main():
    """Entry point for the setup script."""
    print("Setting up linting and formatting tools...")
    files = ensure_config_files()
    if files:
        print("\nConfiguration files created successfully.")
        print("Run 'ruff check .' to lint the codebase.")
        print("Run 'black .' to format the codebase.")
    else:
        print("\nAll configuration files already exist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())