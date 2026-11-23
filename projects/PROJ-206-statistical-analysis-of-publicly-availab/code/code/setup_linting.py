import os
import subprocess
import sys
from pathlib import Path

def ensure_dependencies():
    """Install linting and formatting tools if not present."""
    tools = [
        "ruff",
        "black",
        "pre-commit"
    ]
    for tool in tools:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", tool])
            print(f"Successfully installed/updated {tool}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {tool}: {e}")
            raise

def create_pyproject_config():
    """Create or update pyproject.toml with Black and Ruff configurations."""
    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"
    
    black_config = """
[tool.black]
line-length = 88
target-version = ['py39']
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

    ruff_config = """
[tool.ruff]
# Same as Black
line-length = 88
target-version = "py39"

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]
"""
    
    # Read existing content if it exists
    existing_content = ""
    if pyproject_path.exists():
        existing_content = pyproject_path.read_text()
    
    # Check if sections already exist to avoid duplication
    has_black = "[tool.black]" in existing_content
    has_ruff = "[tool.ruff]" in existing_content
    
    new_content = existing_content
    
    if not has_black:
        new_content += black_config
    
    if not has_ruff:
        new_content += ruff_config
    
    # Write the file
    pyproject_path.write_text(new_content)
    print(f"Updated {pyproject_path} with linting and formatting configurations")

def main():
    """Main entry point for setting up linting and formatting tools."""
    print("Setting up linting and formatting tools...")
    
    # Ensure dependencies are installed
    ensure_dependencies()
    
    # Create configuration files
    create_pyproject_config()
    
    # Create pre-commit config if it doesn't exist
    project_root = Path(__file__).resolve().parent.parent
    pre_commit_path = project_root / ".pre-commit-config.yaml"
    
    if not pre_commit_path.exists():
        pre_commit_config = """
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
- id: black
  language_version: python3
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
- id: ruff
  args: [--fix, --exit-non-zero-on-fix]
"""
        pre_commit_path.write_text(pre_commit_config)
        print(f"Created {pre_commit_path}")
    
    print("Linting and formatting setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())