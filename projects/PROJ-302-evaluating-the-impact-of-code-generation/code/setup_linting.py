import subprocess
import sys
from pathlib import Path
import os
import json

def install_tools():
    """Install ruff and black using pip."""
    print("Installing linting and formatting tools...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black", "--quiet"])
        print("Tools installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing tools: {e}")
        sys.exit(1)

def create_ruff_config(project_root: Path):
    """Create a .ruff.toml configuration file."""
    config_content = """[lint]
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
]

[lint.isort]
known-first-party = ["code"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    config_path = project_root / ".ruff.toml"
    with open(config_path, "w") as f:
        f.write(config_content)
    print(f"Created {config_path}")

def create_black_config(project_root: Path):
    """Create a pyproject.toml section for Black if not present, or a separate .black.toml if preferred.
    We will append to pyproject.toml as per standard practice."""
    pyproject_path = project_root / "pyproject.toml"
    
    black_section = """
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
)/
'''
"""

    if pyproject_path.exists():
        with open(pyproject_path, "r") as f:
            content = f.read()
        if "[tool.black]" not in content:
            with open(pyproject_path, "a") as f:
                f.write(black_section)
            print(f"Appended Black config to {pyproject_path}")
        else:
            print(f"Black config already exists in {pyproject_path}")
    else:
        # Create new pyproject.toml if it doesn't exist
        with open(pyproject_path, "w") as f:
            f.write("[project]\nname = \"llmXive\"\nversion = \"0.1.0\"\n")
            f.write(black_section)
        print(f"Created {pyproject_path} with Black config")

def main():
    """Main entry point to configure linting and formatting."""
    project_root = Path(__file__).resolve().parent.parent
    print(f"Project root: {project_root}")
    
    install_tools()
    create_ruff_config(project_root)
    create_black_config(project_root)
    
    print("Linting and formatting configuration complete.")

if __name__ == "__main__":
    main()