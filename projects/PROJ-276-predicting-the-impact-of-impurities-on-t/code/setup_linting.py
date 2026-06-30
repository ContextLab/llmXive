"""
Setup script to configure linting (ruff) and formatting (black) tools.
Generates configuration files for the project.
"""
import os
import subprocess
import sys
from pathlib import Path

def ensure_directory(path: str) -> None:
    """Ensure the directory for the given path exists."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)

def write_config_file(path: str, content: str) -> None:
    """Write content to a file at the specified path."""
    ensure_directory(path)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Created: {path}")

def setup_ruff_config() -> None:
    """Create ruff.toml configuration file."""
    config_content = """# Ruff configuration
[lint]
# Enable pycodestyle (`E`) and Pyflakes (`F`) codes by default.
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "C90", # mccabe (complexity)
    "N",   # pep8-naming
    "UP",  # pyupgrade
    "S",   # flake8-bandit
    "B",   # flake8-bugbear
    "SIM", # flake8-simplify
    "ARG", # flake8-unused-arguments
    "PTH", # flake8-use-pathlib
]
ignore = [
    "E501", # Line too long (handled by black)
    "S101", # Use of assert detected (often used in tests)
]

# Allow autofix for all enabled rules (when `--fix` is provided).
fixable = ["ALL"]
unfixable = []

# Exclude a few paths.
exclude = [
    ".bzr",
    ".direnv",
    ".eggs",
    ".git",
    ".hg",
    ".mypy_cache",
    ".nox",
    ".pants.d",
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

target-version = "py39"

[lint.per-file-ignores]
"tests/*" = ["S101", "ARG"]
"""
    write_config_file("code/ruff.toml", config_content)

def setup_black_config() -> None:
    """Create pyproject.toml with Black configuration."""
    config_content = """[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
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
    write_config_file("code/pyproject.toml", config_content)

def install_tools() -> None:
    """Install ruff and black if not already installed."""
    print("Checking for ruff and black...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "ruff", "black"])
        print("Tools installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install tools: {e}")
        sys.exit(1)

def main() -> int:
    """Main entry point for the setup script."""
    print("Configuring linting and formatting tools...")
    
    # Ensure we are in the code directory or project root
    # The script is expected to run from the project root
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Install tools
    install_tools()
    
    # Create configuration files
    setup_ruff_config()
    setup_black_config()
    
    print("Linting and formatting configuration complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())