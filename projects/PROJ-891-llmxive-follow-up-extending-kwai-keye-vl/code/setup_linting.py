"""
Task T003: Configure linting (ruff) and formatting (black) tools.

This script creates the configuration files for Ruff and Black in the project root,
ensuring consistent code style and linting rules for the llmXive project.
It also installs the necessary development dependencies into the current environment.
"""
import os
import sys
import subprocess
from pathlib import Path

def ensure_requirements_entry():
    """Ensure ruff and black are in requirements.txt."""
    requirements_file = Path("requirements.txt")
    if not requirements_file.exists():
        print("Error: requirements.txt not found. Please run T002 first.")
        sys.exit(1)

    content = requirements_file.read_text()
    lines = content.splitlines()
    
    # Check for existing entries (case-insensitive check for safety)
    has_ruff = any("ruff" in line.lower() for line in lines)
    has_black = any("black" in line.lower() for line in lines)
    
    new_entries = []
    if not has_ruff:
        new_entries.append("ruff>=0.1.0,<1.0.0")
    if not has_black:
        new_entries.append("black>=23.0.0,<25.0.0")

    if new_entries:
        with open(requirements_file, "a") as f:
            f.write("\n")
            for entry in new_entries:
                f.write(entry + "\n")
        print(f"Updated requirements.txt with: {', '.join(new_entries)}")
    else:
        print("requirements.txt already contains ruff and black.")

def install_dev_dependencies():
    """Install ruff and black using pip."""
    print("Installing ruff and black...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
        print("Successfully installed ruff and black.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)

def write_ruff_config():
    """Create ruff.toml configuration file."""
    config_content = """[lint]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "C90", # mccabe
    "UP",  # pyupgrade
    "N",   # pep8-naming
]
ignore = [
    "E501", # Line too long (handled by Black)
    "D100", # Missing docstring in public module
    "D104", # Missing docstring in public package
    "D107", # Missing docstring in __init__
]

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# Exclude a few specific directories.
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
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

# Same as Black.
line-length = 88

# Allow unused variables when underscore-prefixed.
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

[lint.per-file-ignores]
# Ignore specific rules in test files if needed
"tests/*" = ["D100", "D101", "D102", "D103"]
"""
    ruff_config_path = Path("ruff.toml")
    ruff_config_path.write_text(config_content)
    print(f"Created {ruff_config_path}")

def write_black_config():
    """Create pyproject.toml with Black configuration."""
    # Check if pyproject.toml exists to avoid overwriting
    pyproject_path = Path("pyproject.toml")
    
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content:
            print("pyproject.toml already contains Black configuration. Skipping.")
            return
    
    # Create or append
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.nox
  | \.pants.d
  | \.pytype
  | \.ruff_cache
  | \.svn
  | \.tox
  | \.venv
  | __pypackages__
  | _build
  | buck-out
  | build
  | dist
  | node_modules
  | venv
)/
'''
"""
    if pyproject_path.exists():
        with open(pyproject_path, "a") as f:
            f.write(black_section)
    else:
        pyproject_path.write_text(black_section)
    
    print(f"{'Updated' if pyproject_path.exists() else 'Created'} {pyproject_path} with Black configuration.")

def main():
    """Main entry point for T003."""
    print("Starting T003: Configure linting (ruff) and formatting (black)...")
    
    # 1. Update requirements.txt
    ensure_requirements_entry()
    
    # 2. Install packages
    install_dev_dependencies()
    
    # 3. Write configuration files
    write_ruff_config()
    write_black_config()
    
    print("T003 completed successfully. Ruff and Black are configured.")
    print("To run linter: ruff check .")
    print("To run formatter: black .")

if __name__ == "__main__":
    main()