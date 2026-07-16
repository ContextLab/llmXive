"""
Setup script for linting (Ruff) and formatting (Black) tools.
Creates configuration files (.ruff.toml, pyproject.toml for Black)
and provides a command to verify installation.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd: list[str]) -> bool:
    """Run a shell command and return True if successful."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        return False

def create_ruff_config() -> Path:
    """Create a .ruff.toml configuration file."""
    content = """[lint]
# Select rules: E (pyflakes), F (pycodestyle), W (warnings), I (isort), N (pep8-naming), UP (pyupgrade)
select = ["E", "F", "W", "I", "N", "UP"]
ignore = []

# Allow autofix for all enabled rules
fixable = ["ALL"]
unfixable = []

# Exclude specific files/directories
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
    "data",
    "state",
    "tests"
]

# Same as Black line length
line-length = 88

# Allow unused variables when they start with underscore
dummy-variable-rgx = "^(_+|(_+[a-zA-Z0-9_]*[a-zA-Z0-9]+?))$"

target-version = "py311"

[lint.per-file-ignores]
# Ignore specific rules in test files if needed
"tests/*" = ["S101"]

[format]
# Quote style for strings
quote-style = "double"

# Indent style
indent-style = "space"

# Skip magic trailing comma
skip-magic-trailing-comma = false

# Line ending
line-ending = "auto"
"""
    path = Path(".ruff.toml")
    path.write_text(content)
    print(f"Created configuration: {path}")
    return path

def create_black_config() -> Path:
    """Create a pyproject.toml file with Black configuration if it doesn't exist."""
    path = Path("pyproject.toml")
    if path.exists():
        # Check if [tool.black] section exists
        existing = path.read_text()
        if "[tool.black]" in existing:
            print("pyproject.toml already exists with Black configuration.")
            return path
        else:
            # Append Black config
            black_config = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.nox
  | \\.pants\\.d
  | \\.pytype
  | \\.ruff_cache
  | \\.svn
  | \\.tox
  | \\.venv
  | __pypackages__
  | _build
  | buck-out
  | build
  | dist
  | node_modules
  | venv
  | data
  | state
  | tests
)/
'''
"""
            path.write_text(existing + black_config)
            print(f"Appended Black configuration to: {path}")
    else:
        content = """[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.eggs
  | \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.nox
  | \\.pants\\.d
  | \\.pytype
  | \\.ruff_cache
  | \\.svn
  | \\.tox
  | \\.venv
  | __pypackages__
  | _build
  | buck-out
  | build
  | dist
  | node_modules
  | venv
  | data
  | state
  | tests
)/
'''
"""
        path.write_text(content)
        print(f"Created configuration: {path}")
    return path

def main() -> int:
    """Main entry point for the setup script."""
    print("Setting up linting and formatting tools...")
    
    # Create configuration files
    create_ruff_config()
    create_black_config()

    # Check if tools are installed
    print("\nChecking tool installation...")
    
    tools_installed = True
    
    if not run_command(["ruff", "--version"]):
        print("Ruff is not installed. Installing...")
        if not run_command([sys.executable, "-m", "pip", "install", "ruff"]):
            print("Failed to install Ruff.")
            tools_installed = False
    
    if not run_command(["black", "--version"]):
        print("Black is not installed. Installing...")
        if not run_command([sys.executable, "-m", "pip", "install", "black"]):
            print("Failed to install Black.")
            tools_installed = False

    if not tools_installed:
        print("\nSetup incomplete due to installation errors.")
        return 1

    print("\nConfiguration files created successfully.")
    print("To format code: black code/")
    print("To lint code: ruff check code/")
    return 0

if __name__ == "__main__":
    sys.exit(main())