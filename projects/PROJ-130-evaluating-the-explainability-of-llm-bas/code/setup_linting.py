"""
Setup script to initialize linting and formatting configuration files.
This script generates .ruff.toml and .black (pyproject.toml section) files.
"""
import os
import sys
from pathlib import Path

def create_ruff_config():
    """Create .ruff.toml configuration file."""
    content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # Pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
    "UP", # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.per-file-ignores]
"tests/*" = ["S101"] # assert allowed in tests

[format]
quote-style = "double"
indent-style = "space"
line-ending = "auto"
"""
    path = Path(".ruff.toml")
    path.write_text(content)
    print(f"Created {path}")
    return path

def create_black_config():
    """Create .black configuration (embedded in pyproject.toml if exists, else separate)."""
    # For this project, we create a .black file as requested, 
    # but standard practice is pyproject.toml. We'll create a .black file 
    # that mirrors the standard config for clarity, though ruff/black 
    # primarily read from pyproject.toml or specific config files.
    # Note: Black typically reads from pyproject.toml. We will create 
    # a pyproject.toml entry if it doesn't exist, or append to it.
    # However, the task specifically asks for `.black` config file.
    # We will create a .black file as a reference, but also ensure 
    # pyproject.toml has the config for actual tool usage.
    
    # Let's create a pyproject.toml with black config as the primary source
    # and a .black file as a backup/legacy reference if strictly needed.
    # But standard black usage is via pyproject.toml.
    
    # Creating pyproject.toml with black config:
    pyproject_path = Path("pyproject.toml")
    black_config = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
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
)/
'''
"""
    
    if pyproject_path.exists():
        # Append if not present
        existing = pyproject_path.read_text()
        if "[tool.black]" not in existing:
            pyproject_path.write_text(existing + "\n" + black_config)
            print(f"Appended black config to {pyproject_path}")
        else:
            print(f"Black config already present in {pyproject_path}")
    else:
        pyproject_path.write_text(black_config)
        print(f"Created {pyproject_path} with black config")

    # Also create a .black file as a reference/backup per task request
    # Note: Black doesn't strictly read a file named ".black" by default,
    # but we create it to satisfy the artifact requirement.
    black_file_path = Path(".black")
    black_file_content = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
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
)/
'''
"""
    black_file_path.write_text(black_file_content)
    print(f"Created {black_file_path} (reference)")
    
    return pyproject_path, black_file_path

def create_precommit_config():
    """Create .pre-commit-config.yaml for automated linting."""
    content = """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
"""
    path = Path(".pre-commit-config.yaml")
    path.write_text(content)
    print(f"Created {path}")
    return path

def main():
    """Main entry point to setup linting infrastructure."""
    print("Setting up linting and formatting configuration...")
    create_ruff_config()
    create_black_config()
    create_precommit_config()
    print("Linting setup complete.")
    print("Run 'ruff check .' and 'black --check .' to verify.")

if __name__ == "__main__":
    main()