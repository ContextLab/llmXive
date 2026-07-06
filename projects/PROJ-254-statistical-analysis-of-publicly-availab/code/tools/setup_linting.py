"""
Tool to configure linting (ruff) and formatting (black) tools for the project.

This script creates necessary configuration files:
- pyproject.toml with Black settings
- .ruff.toml with Ruff linting rules
- Updates requirements.txt to include ruff and black
"""
import os
import sys
from pathlib import Path


def create_pyproject_toml() -> str:
    """Create or update pyproject.toml with Black configuration."""
    content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-music-analysis"
version = "0.1.0"
description = "Statistical Analysis of Publicly Available Music Streaming Data for Genre Evolution"
requires-python = ">=3.11"
dependencies = [
    "pandas",
    "numpy",
    "gensim",
    "scikit-learn",
    "statsmodels",
    "matplotlib",
    "plotly",
    "requests",
    "pyarrow",
]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
(
  __pycache__
  | \\.git
  | \\.mypy_cache
  | \\.pytest_cache
  | \\.ruff_cache
  | data/
  | dist/
  | build/
  | venv/
  | .venv/
)
'''

[tool.setuptools]
packages = ["code", "tests"]
"""
    return content


def create_ruff_toml() -> str:
    """Create .ruff.toml with Ruff linting configuration."""
    content = """[ruff]
# Same as Black.
line-length = 88
target-version = "py311"

# Exclude a variety of commonly ignored directories.
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".git-rewrite",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
    ".pytype",
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
    "data/",
]

# Assume Python 3.11
[lint]
# Enable Pyflakes (`F`) and a subset of the pycodestyle (`E`) codes by default.
select = ["E4", "E7", "E9", "F", "I", "N", "UP", "B", "C4", "SIM"]
ignore = []

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[format]
# Like Black, use double quotes for strings.
quote-style = "double"

# Like Black, indent with spaces, rather than tabs.
indent-style = "space"

# Like Black, respect magic trailing commas.
skip-magic-trailing-comma = false

# Like Black, automatically detect the appropriate line ending.
line-ending = "auto"
"""
    return content


def ensure_requirements_entry() -> None:
    """Ensure ruff and black are in requirements.txt."""
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        # Create if it doesn't exist (though T002 should have created it)
        requirements_path.write_text("# Project dependencies\n")
    
    content = requirements_path.read_text()
    lines = content.splitlines()
    
    # Check if ruff and black are already present
    has_ruff = any("ruff" in line.lower() for line in lines)
    has_black = any("black" in line.lower() for line in lines)
    
    new_lines = []
    if not has_ruff:
        new_lines.append("ruff")
    if not has_black:
        new_lines.append("black")
    
    if new_lines:
        # Add new dependencies
        updated_content = content.rstrip() + "\n" + "\n".join(new_lines) + "\n"
        requirements_path.write_text(updated_content)
        print(f"Added to requirements.txt: {', '.join(new_lines)}")
    else:
        print("ruff and black are already in requirements.txt")


def main() -> None:
    """Main entry point for setting up linting and formatting tools."""
    print("Setting up linting (ruff) and formatting (black) tools...")
    
    # Create pyproject.toml
    pyproject_content = create_pyproject_toml()
    pyproject_path = Path("pyproject.toml")
    pyproject_path.write_text(pyproject_content)
    print(f"Created {pyproject_path}")
    
    # Create .ruff.toml
    ruff_content = create_ruff_toml()
    ruff_path = Path(".ruff.toml")
    ruff_path.write_text(ruff_content)
    print(f"Created {ruff_path}")
    
    # Update requirements.txt
    ensure_requirements_entry()
    
    print("\nLinting and formatting tools configured successfully!")
    print("\nTo use them, run:")
    print("  pip install -r requirements.txt")
    print("  ruff check .          # Run linter")
    print("  ruff format .         # Run formatter (or 'black .')")
    print("  ruff check --fix .    # Fix autofixable issues")


if __name__ == "__main__":
    main()