"""
Script to configure linting (ruff) and formatting (black) tools for the project.

This script creates the necessary configuration files in the project root:
- pyproject.toml (containing [tool.black] and [tool.ruff] sections)

It also creates a .pre-commit-config.yaml file to integrate these tools
into the git workflow.
"""
import os
import sys
from pathlib import Path

def create_pyproject_config(root: Path) -> None:
    """Create or update pyproject.toml with black and ruff configuration."""
    config_content = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-eval-bug-fixes"
version = "0.1.0"
description = "Evaluating the Explainability of LLM-Based Bug Fixes"
requires-python = ">=3.11"
dependencies = [
    "transformers==4.36.0",
    "datasets==2.16.0",
    "captum==0.7.0",
    "scikit-learn==1.4.0",
    "pytest==7.4.0",
    "pandas==2.1.0",
    "numpy==1.26.0",
    "evaluate==0.4.1",
    "sentence-transformers==2.2.2",
    "radon==6.0.1",
    "ruff>=0.1.0",
]

[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    # directories
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
target-version = "py311"

# Assume Python 3.11
[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# Exclude a few files/directories.
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
]

# Per-directory configuration
[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"] # Allow assert in tests

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
    
    pyproject_path = root / "pyproject.toml"
    with open(pyproject_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"Created {pyproject_path}")

def create_precommit_config(root: Path) -> None:
    """Create .pre-commit-config.yaml for automated linting and formatting."""
    config_content = """repos:
- repo: https://github.com/psf/black
  rev: 23.12.1
  hooks:
    - id: black
      language_version: python3.11
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.1.9
  hooks:
    - id: ruff
      args: [--fix]
    - id: ruff-format
"""
    
    precommit_path = root / ".pre-commit-config.yaml"
    with open(precommit_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"Created {precommit_path}")

def main() -> int:
    """Main entry point for the script."""
    # Determine project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    root = code_dir.parent
    
    print(f"Configuring linting and formatting in: {root}")
    
    try:
        create_pyproject_config(root)
        create_precommit_config(root)
        
        print("\nConfiguration complete!")
        print("\nTo use the tools, run:")
        print("  pip install -r code/requirements.txt")
        print("  pre-commit install")
        print("\nTo run manually:")
        print("  ruff check .")
        print("  black .")
        
        return 0
    except Exception as e:
        print(f"Error during configuration: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
