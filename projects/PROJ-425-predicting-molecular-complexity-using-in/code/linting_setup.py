"""
Linting and Formatting Setup Script.

This module provides functions to install linting/formatter dependencies
and create configuration files for ruff and black.
"""
import os
import subprocess
import sys
from pathlib import Path


def install_dependencies():
    """
    Install ruff and black using pip.
    Returns True if successful, False otherwise.
    """
    tools = ["ruff", "black"]
    for tool in tools:
        try:
            print(f"Installing {tool}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", tool])
            print(f"{tool} installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {tool}: {e}")
            return False
    return True


def create_config_files():
    """
    Create configuration files for ruff and black.
    - ruff.toml (or .ruff.toml) for linting rules
    - pyproject.toml [tool.black] section for formatting
    """
    project_root = Path(__file__).parent.parent
    ruff_config_path = project_root / "ruff.toml"
    pyproject_path = project_root / "pyproject.toml"

    # Create ruff.toml
    ruff_content = """# Ruff Configuration for PROJ-425
[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # Line too long (handled by black)
    "B008", # Do not perform function call in argument defaults (common in data loading)
]

[lint.per-file-ignores]
"__init__.py" = ["F401"] # Ignore unused imports in __init__.py

[format]
# Use double quotes for strings
quote-style = "double"
# Indent with spaces
indent-style = "space"
# Respect magic trailing commas
skip-magic-trailing-comma = false
# Line length matching black's default
line-length = 88
"""

    with open(ruff_config_path, "w", encoding="utf-8") as f:
        f.write(ruff_content)
    print(f"Created {ruff_config_path}")

    # Create/Update pyproject.toml for Black
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    # The following are specific to Black, you probably don't want those.
    | build
    | dist
    | .eggs
)/
'''
"""

    if pyproject_path.exists():
        # Append to existing file
        with open(pyproject_path, "a", encoding="utf-8") as f:
            f.write(black_section)
        print(f"Appended Black config to {pyproject_path}")
    else:
        # Create new file with minimal header
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(f"[project]\nname = 'proj-425'\nversion = '0.1.0'\n{black_section}")
        print(f"Created {pyproject_path} with Black config")

    return True


def main():
    """Main entry point for linting setup."""
    print("Starting Linting and Formatting Setup...")
    
    if not install_dependencies():
        print("Error: Failed to install dependencies.")
        sys.exit(1)
    
    if not create_config_files():
        print("Error: Failed to create configuration files.")
        sys.exit(1)
    
    print("Linting and Formatting setup complete.")
    print("Run 'ruff check .' to lint and 'black .' to format.")


if __name__ == "__main__":
    main()