"""
Configuration management for linting (ruff) and formatting (black) tools.
Ensures pyproject.toml contains the necessary sections and settings.
"""
import os
import sys
from pathlib import Path

def ensure_pyproject_toml():
    """
    Creates or updates pyproject.toml with configuration for ruff and black.
    """
    root = Path(__file__).resolve().parent.parent
    pyproject_path = root / "pyproject.toml"

    # Define the required configuration sections
    config_content = """[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ambient-temp-moral-speed"
version = "0.1.0"
description = "Analysis of ambient temperature influence on moral decision speed"
requires-python = ">=3.9"
dependencies = [
    "pandas",
    "numpy",
    "statsmodels",
    "scikit-learn",
    "requests",
    "pyyaml",
    "seaborn",
    "matplotlib",
    "geopandas",
    "cdsapi",
]

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
include = '\\.pyi?$'
extend-exclude = '''
# A regex to exclude files
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.ruff]
# Same as Black.
line-length = 88
target-version = "py39"

# Assume Python 3.9
[tool.ruff.lint]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "ARG", "SIM"]
ignore = ["E501", "B008"]

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# Exclude a few files/directories.
extend-exclude = [
    "__pycache__",
    ".eggs",
    ".git",
    ".mypy_cache",
    ".tox",
    ".venv",
    "build",
    "dist",
]

[tool.ruff.format]
# Like Black, use double quotes for strings.
quote-style = "double"

# Like Black, indent with spaces, rather than tabs.
indent-style = "space"

# Like Black, respect magic trailing commas.
skip-magic-trailing-comma = false

# Like Black, automatically detect the appropriate line ending.
line-ending = "auto"
"""

    if not pyproject_path.exists():
        with open(pyproject_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"Created {pyproject_path} with ruff and black configuration.")
    else:
        # Check if sections exist
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            content = f.read()

        needs_update = False
        if "[tool.black]" not in content:
            needs_update = True
        if "[tool.ruff]" not in content:
            needs_update = True

        if needs_update:
            with open(pyproject_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            print(f"Updated {pyproject_path} with missing ruff/black sections.")
        else:
            print(f"{pyproject_path} already contains ruff and black configuration.")

    return pyproject_path

def main():
    """
    Main entry point for the configuration script.
    """
    try:
        path = ensure_pyproject_toml()
        print(f"Linting and formatting configuration verified at: {path}")
        return 0
    except Exception as e:
        print(f"Error configuring linting tools: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())