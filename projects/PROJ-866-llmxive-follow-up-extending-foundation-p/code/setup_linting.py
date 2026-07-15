"""
Setup script for linting (Ruff) and formatting (Black) tools.
Creates configuration files in the project root and updates .gitignore.
"""
import os
import sys
from pathlib import Path
from typing import List

def create_linting_config() -> Path:
    """Create ruff.toml configuration file."""
    content = """# Ruff configuration
[lint]
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
    "E501", # line-too-long (handled by Black)
    "B008", # do not perform function calls in argument defaults
]

[lint.isort]
known-first-party = ["code"]
force-single-line = true

[lint.per-file-ignores]
"__init__.py" = ["F401"]
"""
    path = Path("ruff.toml")
    path.write_text(content)
    return path

def create_formatting_config() -> Path:
    """Create pyproject.toml with Black configuration."""
    # Check if pyproject.toml exists
    pyproject_path = Path("pyproject.toml")
    
    black_config = """[tool.black]
line-length = 88
target-version = ['py39']
include = '\\.pyi?$'
"""
    
    if pyproject_path.exists():
        existing = pyproject_path.read_text()
        if "[tool.black]" not in existing:
            # Append to existing file
            pyproject_path.write_text(existing + "\n" + black_config)
        return pyproject_path
    else:
        # Create new file
        pyproject_path.write_text(black_config)
        return pyproject_path

def create_ruffignore() -> Path:
    """Create .ruffignore file."""
    content = """# Directories to ignore for Ruff
__pycache__/
.venv/
venv/
.env/
.git/
"""
    path = Path(".ruffignore")
    path.write_text(content)
    return path

def create_gitignore_update() -> Path:
    """Update .gitignore with linting/formatting artifacts if not present."""
    gitignore_path = Path(".gitignore")
    new_entries = """
# Linting and Formatting
.ruff_cache/
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
"""
    
    if gitignore_path.exists():
        existing = gitignore_path.read_text()
        if ".ruff_cache/" not in existing:
            gitignore_path.write_text(existing + new_entries)
    else:
        gitignore_path.write_text(new_entries)
    
    return gitignore_path

def main() -> int:
    """Main entry point for setup script."""
    print("Setting up linting and formatting tools...")
    
    try:
        # Create Ruff config
        ruff_path = create_linting_config()
        print(f"Created: {ruff_path}")
        
        # Create Black config
        black_path = create_formatting_config()
        print(f"Created/Updated: {black_path}")
        
        # Create Ruff ignore
        ruffignore_path = create_ruffignore()
        print(f"Created: {ruffignore_path}")
        
        # Update .gitignore
        gitignore_path = create_gitignore_update()
        print(f"Updated: {gitignore_path}")
        
        print("\nLinting and formatting tools configured successfully!")
        print("To run Ruff: ruff check .")
        print("To run Black: black .")
        print("To format and check: ruff check . && black .")
        
        return 0
    except Exception as e:
        print(f"Error during setup: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())