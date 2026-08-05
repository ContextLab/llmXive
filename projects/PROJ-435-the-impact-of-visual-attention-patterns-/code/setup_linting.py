"""
Setup linting and formatting tools for the project.

This script creates configuration files for ruff (linting) and black (formatting).
"""
import os
import sys
import subprocess
from pathlib import Path

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def run_command(cmd: list) -> bool:
    """Run a shell command and return True if successful."""
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"stderr: {e.stderr}")
        return False

def create_ruff_config(project_root: Path) -> None:
    """Create a ruff configuration file."""
    ruff_config_path = project_root / "ruff.toml"
    config_content = """# Ruff configuration for llmXive project

# Target Python version
target-version = "py311"

# Line length for linting checks
line-length = 100

# Exclude directories
exclude = [
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "build",
    "dist",
    "data",
    "state",
    "output",
]

[lint]
# Enable specific rules
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "RUF", # Ruff-specific rules
]

# Ignore specific rules if needed
ignore = [
    "E501", # Line too long (handled by black)
    "B008", # Do not perform function call in argument defaults
]

# Allow autofix for all enabled rules
fixable = ["ALL"]
unfixable = []

[lint.per-file-ignores]
# Allow certain rules to be ignored in specific files
"__init__.py" = ["F401"]

[lint.isort]
# Isort configuration
known-first-party = ["code", "tests"]
force-single-line = false
lines-between-types = 0
lines-after-imports = 2

[format]
# Black-compatible formatting
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    with open(ruff_config_path, 'w') as f:
        f.write(config_content)
    print(f"Created ruff configuration: {ruff_config_path}")

def create_black_config(project_root: Path) -> None:
    """Create a black configuration file."""
    black_config_path = project_root / "pyproject.toml"
    
    # Check if pyproject.toml exists and read it
    if black_config_path.exists():
        with open(black_config_path, 'r') as f:
            content = f.read()
    else:
        content = ""

    # Check if [tool.black] section already exists
    if "[tool.black]" in content:
        print(f"[tool.black] section already exists in {black_config_path}")
        return

    # Add black configuration
    black_section = """
[tool.black]
line-length = 100
target-version = ['py311']
exclude = '''
/(
    \.git
  | \.venv
  | venv
  | __pycache__
  | build
  | dist
  | data
  | state
  | output
)/
'''
include = '\.pyi?$'
"""
    
    # Append the black section to the content
    if content and not content.endswith('\n'):
        content += '\n'
    content += black_section

    with open(black_config_path, 'w') as f:
        f.write(content)
    print(f"Updated black configuration: {black_config_path}")

def main() -> int:
    """Main function to setup linting and formatting tools."""
    project_root = get_project_root()
    print(f"Setting up linting and formatting tools for project at: {project_root}")

    # Create ruff configuration
    create_ruff_config(project_root)

    # Create black configuration
    create_black_config(project_root)

    # Try to install the tools if not already installed
    print("\nAttempting to install linting and formatting tools...")
    tools = [
        ["pip", "install", "--upgrade", "ruff"],
        ["pip", "install", "--upgrade", "black"],
    ]

    for cmd in tools:
        if not run_command(cmd):
            print(f"Warning: Could not install {' '.join(cmd)}")
            print("Please install manually: pip install ruff black")

    print("\nSetup complete!")
    print("To run ruff: ruff check .")
    print("To run black: black .")
    print("To run ruff format: ruff format .")

    return 0

if __name__ == "__main__":
    sys.exit(main())