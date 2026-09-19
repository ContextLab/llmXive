"""
Script to configure linting (ruff) and formatting (black) tools.
Creates necessary configuration files and installs dependencies.
"""
import os
import subprocess
import sys
from pathlib import Path

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def write_config_file(path: Path, content: str) -> None:
    """Write content to a configuration file."""
    ensure_directory(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {path}")

def setup_ruff_config(project_root: Path) -> None:
    """Create ruff configuration file."""
    config_content = """
# Standalone ruff configuration file
line-length = 88
target-version = "py39"

select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
]
ignore = [
    "E501",  # line too long (black handles this)
    "B008",  # do not perform function calls in argument defaults
    "C901",  # too complex
]

[isort]
known-first-party = ["src", "scripts", "tests"]
force-sort-within-sections = true
combine-as-imports = true
"""
    write_config_file(project_root / "ruff.toml", config_content)

def setup_black_config(project_root: Path) -> None:
    """Create black configuration file in pyproject.toml."""
    # Read existing pyproject.toml if it exists
    pyproject_path = project_root / "pyproject.toml"
    
    if pyproject_path.exists():
        with open(pyproject_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-mgb2-impurity"
version = "0.1.0"
description = "Predicting the impact of impurities on the superconductivity of Magnesium Diboride"
requires-python = ">=3.9"
"""

    # Add black configuration if not present
    if "[tool.black]" not in content:
        black_config = """
[tool.black]
line-length = 88
target-version = ["py39", "py310", "py311"]
include = '\\.pyi?$'
extend-exclude = '''
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
        content += black_config
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated: {pyproject_path} with Black configuration")
    else:
        print(f"Black configuration already exists in {pyproject_path}")

def install_tools() -> None:
    """Install ruff and black if not already installed."""
    print("Checking and installing linting tools...")
    
    tools = [
        ("ruff", "ruff"),
        ("black", "black")
    ]
    
    for pkg, cmd in tools:
        try:
            subprocess.run([sys.executable, "-m", "pip", "show", pkg], 
                         check=True, capture_output=True)
            print(f"✓ {pkg} is already installed")
        except subprocess.CalledProcessError:
            print(f"Installing {pkg}...")
            subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=True)
            print(f"✓ {pkg} installed successfully")

def main() -> None:
    """Main entry point for setup_linting script."""
    print("Setting up linting and formatting tools...")
    
    # Determine project root (parent of code/ directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent
    
    # Setup configuration files
    setup_ruff_config(project_root)
    setup_black_config(project_root)
    
    # Install tools
    install_tools()
    
    print("\nLinting and formatting setup complete!")
    print("Usage:")
    print("  - Format code: black .")
    print("  - Lint code: ruff check .")
    print("  - Fix linting issues: ruff check . --fix")

if __name__ == "__main__":
    main()
