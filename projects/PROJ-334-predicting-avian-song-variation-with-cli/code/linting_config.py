"""
Linting and Formatting Configuration Generator for llmXive project.

This module generates configuration files for Black (formatter) and Ruff (linter)
to ensure consistent code style across the project.
"""
import os
from pathlib import Path

# Configuration constants
BLACK_VERSION = "24.4.2"
RUFF_VERSION = "0.4.8"
TARGET_PYTHON_VERSION = "3.10"
LINE_LENGTH = 88


def get_black_config_path() -> Path:
    """Return the path to the black configuration file."""
    return Path("pyproject.toml")


def get_ruff_config_path() -> Path:
    """Return the path to the ruff configuration file."""
    return Path("pyproject.toml")


def write_config_files() -> None:
    """
    Write Black and Ruff configuration to pyproject.toml.

    Creates a pyproject.toml file with sections for:
    - [tool.black]: Formatting configuration
    - [tool.ruff]: Linting configuration

    The configuration enforces:
    - Line length of 88 characters
    - Python 3.10+ target
    - Common linting rules (E, F, W, I, N, UP, B, C4, SIM, PL)
    - Ignored rules for specific cases (e.g., line too long in docstrings)
    """
    config_content = f"""[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "llmXive-avian-song"
version = "0.1.0"
description = "Predicting avian song variation with climatic and geographic factors"
requires-python = ">={TARGET_PYTHON_VERSION}"
dependencies = [
    "pandas",
    "numpy",
    "scikit-learn",
    "statsmodels",
    "scipy",
    "matplotlib",
    "seaborn",
    "pyyaml",
    "requests",
    "rasterio",
    "geopandas",
    "pyproj",
]

[tool.black]
line-length = {LINE_LENGTH}
target-version = ['py{TARGET_PYTHON_VERSION.replace('.', '')}']
include = '\\.pyi?$'
extend-exclude = '''
/(
  # directories
  \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
  | data
  | __pycache__
)/
'''

[tool.ruff]
# Same as Black.
line-length = {LINE_LENGTH}
target-version = "py{TARGET_PYTHON_VERSION.replace('.', '')}"

# Exclude a variety of commonly ignored directories.
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
    "data",
    "venv",
    "__pycache__",
]

# Assume Python 3.10
[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "N",  # pep8-naming
    "UP", # pyupgrade
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "SIM",# flake8-simplify
    "PL", # Pylint
]
ignore = [
    "E501", # Line too long (handled by black)
    "PLR0913", # Too many arguments to function call
    "PLR0915", # Too many statements
    "PLR2004", # Magic value used in comparison
    "SIM105", # Use contextlib.suppress instead of try/except
]

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"] # Allow asserts in tests
"code/*" = ["D100", "D101", "D102", "D103"] # Allow missing docstrings in some code files during dev

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""

    output_path = Path("pyproject.toml")
    output_path.write_text(config_content)
    print(f"Configuration written to {output_path}")


def main() -> None:
    """Entry point for generating linting and formatting configurations."""
    write_config_files()
    print("Linting (Ruff) and Formatting (Black) configurations have been generated.")
    print("To use them, run:")
    print("  ruff check .        # Lint code")
    print("  ruff format .       # Format code")
    print("  black --check .     # Check formatting")
    print("  black .             # Apply formatting")


if __name__ == "__main__":
    main()