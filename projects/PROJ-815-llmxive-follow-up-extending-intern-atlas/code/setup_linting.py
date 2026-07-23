"""
Setup script for configuring linting (ruff) and formatting (black) tools.
This script generates the necessary configuration files for the project.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Main function to generate configuration files for ruff and black.
    """
    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"

    # Check if pyproject.toml exists
    if pyproject_path.exists():
        print(f"Warning: {pyproject_path} already exists. Skipping generation.")
        return 0

    # Define the content for pyproject.toml
    config_content = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.ruff]
# Same as Black.
line-length = 88
indent-width = 4
target-version = "py311"

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[tool.ruff.lint]
# Enable Pyflakes (`F`) and a subset of the pycodestyle (`E`) codes by default.
select = ["E4", "E7", "E9", "F", "I", "N", "UP"]
ignore = []

# Allow fix for all enabled rules (when `--fix`) is provided.
fixable = ["ALL"]
unfixable = []

# Exclude a few files.
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

# Assume Python 3.11.
target-version = "py311"

[tool.ruff.lint.per-file-ignores]
# Ignore `E402` (import order) in `__init__.py` files.
"__init__.py" = ["E402"]
"""

    # Write the configuration file
    try:
        pyproject_path.write_text(config_content)
        print(f"Successfully created {pyproject_path}")
        
        # Create a .pre-commit-config.yaml for pre-commit hooks
        pre_commit_path = project_root / ".pre-commit-config.yaml"
        pre_commit_content = """repos:
  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
- id: black
  language_version: python3.11
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.5
    hooks:
- id: ruff
  args: [--fix]
- id: ruff-format
"""
        pre_commit_path.write_text(pre_commit_content)
        print(f"Successfully created {pre_commit_path}")
        
        return 0
    except Exception as e:
        print(f"Error creating configuration files: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())