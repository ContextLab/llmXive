"""
Configuration and setup script for linting (ruff) and formatting (black) tools.
This script generates the necessary configuration files (.toml) and a setup script
to install and configure the tools within the project environment.
"""
import os
import subprocess
import sys
from pathlib import Path

def ensure_config_dir():
    """Ensure the project root exists."""
    root = Path(__file__).resolve().parent.parent
    return root

def write_pyproject_toml(root: Path):
    """
    Write or update pyproject.toml with [tool.black] and [tool.ruff] sections.
    """
    toml_path = root / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
(
  __pycache__
  | .git
  | .venv
  | venv
  | build
  | dist
)
'''

[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
    "ARG",# flake8-unused-arguments
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "ARG001", # unused arguments in __init__ or __new__ often acceptable in data classes
]
extend-exclude = [
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "build",
    "dist",
]

[tool.ruff.isort]
known-first-party = ["setup_directories", "setup_git"]
"""

    if toml_path.exists():
        content = toml_path.read_text()
        # Simple check to avoid duplicating sections if they already exist
        if "[tool.black]" not in content:
            content += black_section
        elif "[tool.ruff]" not in content:
            # Find position to insert ruff after black
            # Assuming black is present, append ruff
            content += black_section
        toml_path.write_text(content)
    else:
        toml_path.write_text(f"# Project Configuration\n{black_section}")
    
    print(f"Updated/created {toml_path}")

def create_install_script(root: Path):
    """
    Create a helper script to install and format the codebase.
    """
    script_path = root / "scripts" / "setup_linting.sh"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    
    script_content = """#!/bin/bash
set -e

echo "Installing linting and formatting tools..."
pip install black ruff

echo "Formatting code with black..."
black code/ tests/

echo "Linting code with ruff..."
ruff check code/ tests/

echo "Linting complete."
"""
    script_path.write_text(script_content)
    script_path.chmod(0o755)
    print(f"Created executable script: {script_path}")

def main():
    root = ensure_config_dir()
    print(f"Configuring linting and formatting for project root: {root}")
    
    write_pyproject_toml(root)
    create_install_script(root)
    
    print("\nConfiguration complete.")
    print("To apply formatting and linting, run: ./scripts/setup_linting.sh")
    print("Or manually: black code/ tests/ && ruff check code/ tests/")

if __name__ == "__main__":
    main()