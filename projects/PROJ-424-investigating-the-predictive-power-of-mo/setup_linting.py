"""
Setup script to initialize linting and formatting configurations.
This script ensures that configuration files (pyproject.toml, .pre-commit-config.yaml)
exist with the correct settings for Ruff and Black as per the project requirements.
"""
import os
from pathlib import Path

def ensure_config_files():
    """Ensure configuration files for linting and formatting exist."""
    project_root = Path(__file__).parent
    pyproject_path = project_root / "pyproject.toml"
    precommit_path = project_root / ".pre-commit-config.yaml"

    # Check if pyproject.toml exists
    if not pyproject_path.exists():
        print(f"Creating {pyproject_path}...")
        with open(pyproject_path, "w") as f:
            f.write(pyproject_content)
    else:
        print(f"{pyproject_path} already exists. Skipping creation.")

    # Check if .pre-commit-config.yaml exists
    if not precommit_path.exists():
        print(f"Creating {precommit_path}...")
        with open(precommit_path, "w") as f:
            f.write(precommit_content)
    else:
        print(f"{precommit_path} already exists. Skipping creation.")

    print("\nLinting and formatting configuration complete.")
    print("Run 'pip install -e .' to install dependencies if not already done.")
    print("Run 'pre-commit install' to install git hooks.")

pyproject_content = """
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "investigating-md-diffusion-predictive-power"
version = "0.1.0"
description = "Investigating the Predictive Power of Molecular Dynamics for Estimating Diffusion Coefficients"
requires-python = ">=3.11"
dependencies = [
    "gromacs",
    "mdanalysis",
    "numpy",
    "pandas",
    "scipy",
    "matplotlib",
    "seaborn",
    "scikit-learn",
    "pyyaml",
    "ruff",
    "black",
]

[tool.ruff]
# Target Python version
target-version = "py311"

# Line length for formatting
line-length = 88

# Exclude common directories
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "__pypackages__",
    "_build",
    "buck-out",
    "build",
    "dist",
    "node_modules",
    "venv",
    "data",
    "figures",
]

[tool.ruff.lint]
# Enable specific rules
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]

# Ignore specific rules if necessary
ignore = [
    "E501", # Line too long (handled by black)
    "B008", # Do not perform function calls in argument defaults (common in dataclasses)
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"] # Allow assertions in tests

[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
    | \\.hg
    | \\.mypy_cache
    | \\.tox
    | \\.venv
    | _build
    | buck-out
    | build
    | dist
    | data
    | figures
)/
'''

[tool.setuptools]
packages = ["code", "tests"]
package-dir = {"" = "code"}

[tool.setuptools.packages.find]
where = ["."]
include = ["code*"]
namespaces = false
"""

precommit_content = """
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1024'] # Prevent large files in repo

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11
"""

if __name__ == "__main__":
    ensure_config_files()