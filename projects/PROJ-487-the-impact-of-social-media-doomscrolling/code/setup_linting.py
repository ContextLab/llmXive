"""
Setup script for linting and formatting tools.

This script generates configuration files for flake8 and black
to ensure consistent code style across the project.
"""
import os
import sys
from pathlib import Path

def create_gitignore_entry():
    """Ensure .gitignore includes necessary linting artifacts."""
    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        gitignore_path.touch()
    
    content = gitignore_path.read_text()
    entries = [
        "\n# Linting and Formatting\n",
        ".mypy_cache/\n",
        "__pycache__/\n",
        "*.pyc\n",
        ".coverage\n",
        "htmlcov/\n",
        ".tox/\n",
    ]
    
    needs_update = False
    for entry in entries:
        if entry.strip() not in content:
            needs_update = True
            content += entry
    
    if needs_update:
        gitignore_path.write_text(content)
        print("Updated .gitignore with linting artifacts.")
    else:
        print(".gitignore already contains linting artifacts.")

def create_flake8_config():
    """Create .flake8 configuration file."""
    config_path = Path(".flake8")
    
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info,
    venv,
    .venv,
    .tox
per-file-ignores =
    # Allow unused imports in __init__.py
    code/__init__.py:F401
    # Allow unused imports in tests
    tests/*:F401
"""
    
    config_path.write_text(config_content)
    print("Created .flake8 configuration.")

def create_black_config():
    """Create pyproject.toml [tool.black] section if missing."""
    pyproject_path = Path("pyproject.toml")
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.mypy_cache
  | \\.tox
  | venv
  | .venv
  | build
  | dist
  | \\.eggs
  | \\.egg-info
)/
'''
"""
    
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" not in content:
            content += black_section
            pyproject_path.write_text(content)
            print("Added [tool.black] section to pyproject.toml.")
        else:
            print("[tool.black] section already exists in pyproject.toml.")
    else:
        pyproject_path.write_text(f"[project]\nname = \"llmXive-doombscrolling\"\nversion = \"0.1.0\"\n" + black_section)
        print("Created pyproject.toml with [tool.black] section.")

def create_isort_config():
    """Create isort configuration in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    
    isort_section = """
[tool.isort]
profile = "black"
line_length = 88
known_first_party = ["code", "tests"]
skip = [".git", "__pycache__", "build", "dist", ".eggs", ".egg-info", "venv", ".venv", ".tox"]
"""
    
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.isort]" not in content:
            content += isort_section
            pyproject_path.write_text(content)
            print("Added [tool.isort] section to pyproject.toml.")
        else:
            print("[tool.isort] section already exists in pyproject.toml.")
    else:
        # If pyproject.toml doesn't exist, create it
        pyproject_path.write_text(f"[project]\nname = \"llmXive-doombscrolling\"\nversion = \"0.1.0\"\n" + isort_section)
        print("Created pyproject.toml with [tool.isort] section.")

def main():
    """Main entry point for setup script."""
    print("Setting up linting and formatting tools...")
    
    try:
        create_gitignore_entry()
        create_flake8_config()
        create_black_config()
        create_isort_config()
        
        print("\nLinting and formatting configuration complete!")
        print("\nTo run linting:")
        print("  flake8 code/ tests/")
        print("\nTo run formatting:")
        print("  black code/ tests/")
        print("  isort code/ tests/")
        
    except Exception as e:
        print(f"Error during setup: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()