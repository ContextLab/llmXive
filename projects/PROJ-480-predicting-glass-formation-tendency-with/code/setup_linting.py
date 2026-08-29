"""
Linting and Formatting Configuration Setup Script.

This script generates configuration files for Ruff (linting) and Black (formatting)
and updates pyproject.toml and .gitignore as needed.
"""

import os
import sys
from pathlib import Path


def create_pyproject_config(root: Path) -> None:
    """
    Create or update pyproject.toml with Ruff and Black configuration.
    
    Args:
        root: The project root directory.
    """
    pyproject_path = root / "pyproject.toml"
    
    # Configuration content for Ruff and Black
    config_section = """
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
  | node_modules
)/
'''

[tool.ruff]
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
]

# Assume Python 3.11
[tool.ruff.lint]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = ["E", "F", "I", "D", "N", "W", "UP", "YTT", "B", "C4", "SIM", "TID"]
ignore = [
    "D100", # Missing docstring in public module
    "D104", # Missing docstring in public package
    "D105", # Missing docstring in magic method
]

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.lint.pydocstyle]
convention = "google"
"""

    # Check if pyproject.toml exists
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        # Check if tool sections already exist to avoid duplication
        if "[tool.black]" in content or "[tool.ruff]" in content:
            print("pyproject.toml already contains tool configurations.")
            return
        
        # Append new configuration
        with open(pyproject_path, "a", encoding="utf-8") as f:
            f.write(config_section)
    else:
        # Create new file with configuration
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(config_section)
    
    print(f"Updated {pyproject_path} with Ruff and Black configuration.")


def create_gitignore_entries(root: Path) -> None:
    """
    Add linting and formatting related entries to .gitignore.
    
    Args:
        root: The project root directory.
    """
    gitignore_path = root / ".gitignore"
    
    entries = """
# Linting and Formatting
.ruff_cache/
.black_cache/
"""
    
    if gitignore_path.exists():
        content = gitignore_path.read_text()
        if ".ruff_cache/" not in content:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(entries)
            print("Updated .gitignore with linting cache entries.")
        else:
            print(".gitignore already contains linting cache entries.")
    else:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(entries)
        print("Created .gitignore with linting cache entries.")


def main() -> None:
    """Main entry point for the setup script."""
    # Determine project root (assume running from project root or parent of code/)
    if "code" in os.getcwd():
        root = Path(os.getcwd()).parent
    else:
        root = Path(os.getcwd())
    
    print(f"Setting up linting and formatting in: {root}")
    
    create_pyproject_config(root)
    create_gitignore_entries(root)
    
    print("Setup complete. Run 'pip install ruff black' if not already installed.")
    print("Usage:")
    print("  Format code: black code/ tests/")
    print("  Lint code: ruff check code/ tests/")
    print("  Fix linting issues: ruff check --fix code/ tests/")


if __name__ == "__main__":
    main()