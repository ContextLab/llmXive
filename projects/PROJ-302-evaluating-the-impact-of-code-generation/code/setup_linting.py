"""
Script to install and configure linting (ruff) and formatting (black) tools.
This script updates requirements.txt and generates configuration files.
"""
import subprocess
import sys
from pathlib import Path

# Ensure we are running from the project root or handle relative paths correctly
# Assuming the script is run as `python code/setup_linting.py` from root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def install_tools():
    """Install ruff and black if not already installed."""
    print("Installing linting and formatting tools...")
    tools = ["ruff", "black"]
    for tool in tools:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", tool])
            print(f"Successfully installed {tool}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {tool}: {e}")
            sys.exit(1)
    print("All tools installed successfully.")

def create_ruff_config():
    """Create a .ruff.toml configuration file."""
    config_path = PROJECT_ROOT / ".ruff.toml"
    content = """
# Ruff configuration
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
    "C901", # too complex
]

# Allow autofix for all enabled rules (when `--fix` is provided)
fixable = ["ALL"]
unfixable = []

# Exclude a few files
extend-exclude = ["__pycache__", "*.egg-info", ".git", "venv", "data"]

# Same as Black.
line-length = 88
target-version = "py311"

[per-file-ignores]
# Allow imports in __init__.py
"__init__.py" = ["F401"]
"""
    with open(config_path, "w") as f:
        f.write(content.strip() + "\n")
    print(f"Created {config_path}")

def create_black_config():
    """Create a pyproject.toml section for Black if not present, or a standalone config."""
    # We will add to pyproject.toml if it exists, otherwise create it with just black config
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    
    black_section = """
[tool.black]
line-length = 88
target-version = ['py311']
include = '\\.pyi?$'
extend-exclude = '''
/(
    \\.__pycache__
    | \\.git
    | \\.mypy_cache
    | \\.venv
    | data
)/
'''
"""
    
    if pyproject_path.exists():
        # Append to existing file
        with open(pyproject_path, "a") as f:
            f.write("\n" + black_section.strip() + "\n")
    else:
        # Create new file with just black config (and maybe a minimal header)
        with open(pyproject_path, "w") as f:
            f.write("[build-system]\nrequires = [\"setuptools>=42\", \"wheel\"]\nbuild-backend = \"setuptools.build_meta\"\n\n")
            f.write(black_section.strip() + "\n")
    
    print(f"Updated/Created {pyproject_path} with Black configuration")

def main():
    """Main entry point."""
    install_tools()
    create_ruff_config()
    create_black_config()
    print("Linting and formatting configuration complete.")

if __name__ == "__main__":
    main()