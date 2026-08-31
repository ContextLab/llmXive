import os
import sys
from pathlib import Path
import tomllib
import configparser
import argparse

def check_file_exists(path: Path) -> bool:
    """Check if a file exists at the given path."""
    return path.exists()

def validate_ruff_config(config_path: Path) -> bool:
    """Validate that ruff configuration exists and is valid."""
    if not config_path.exists():
        return False
    try:
        # ruff.toml or .ruff.toml should be valid TOML
        with open(config_path, "rb") as f:
            tomllib.load(f)
        return True
    except Exception:
        return False

def validate_pyproject_black(config_path: Path) -> bool:
    """Validate that black configuration exists in pyproject.toml."""
    if not config_path.exists():
        return False
    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        return "tool" in data and "black" in data["tool"]
    except Exception:
        return False

def validate_flake8_config(config_path: Path) -> bool:
    """Validate that flake8 configuration exists."""
    if not config_path.exists():
        return False
    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        return "flake8" in config or "flake" in config
    except Exception:
        return False

def create_ruff_config(project_root: Path) -> None:
    """Create a .ruff.toml configuration file."""
    config_content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[lint.per-file-ignores]
"__init__.py" = ["F401"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    config_path = project_root / ".ruff.toml"
    with open(config_path, "w") as f:
        f.write(config_content)

def create_black_config(project_root: Path) -> None:
    """Create a pyproject.toml configuration for black."""
    config_path = project_root / "pyproject.toml"
    
    # Read existing content if any
    existing_content = ""
    if config_path.exists():
        with open(config_path, "r") as f:
            existing_content = f.read()
    
    # Check if [tool.black] section already exists
    if "[tool.black]" in existing_content:
        return  # Already configured
    
    # Append black configuration
    black_config = """
[tool.black]
line-length = 88
target-version = ['py310']
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
    
    with open(config_path, "a") as f:
        f.write(black_config)

def create_flake8_config(project_root: Path) -> None:
    """Create a .flake8 configuration file."""
    config_content = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist,.eggs
ignore = E501,B008
"""
    config_path = project_root / ".flake8"
    with open(config_path, "w") as f:
        f.write(config_content)

def install_linting_tools() -> None:
    """Install linting and formatting tools."""
    tools = [
        "ruff",
        "black",
        "flake8",
    ]
    for tool in tools:
        os.system(f"pip install {tool}")

def main() -> None:
    """Main function to set up linting and formatting tools."""
    project_root = Path(__file__).parent.parent
    
    print("Setting up linting and formatting tools...")
    
    # Install tools
    install_linting_tools()
    
    # Create configuration files
    create_ruff_config(project_root)
    create_black_config(project_root)
    create_flake8_config(project_root)
    
    # Validate configurations
    ruff_config = project_root / ".ruff.toml"
    pyproject_config = project_root / "pyproject.toml"
    flake8_config = project_root / ".flake8"
    
    if validate_ruff_config(ruff_config):
        print("✓ Ruff configuration created and validated")
    else:
        print("✗ Failed to create Ruff configuration")
        sys.exit(1)
    
    if validate_pyproject_black(pyproject_config):
        print("✓ Black configuration created and validated")
    else:
        print("✗ Failed to create Black configuration")
        sys.exit(1)
    
    if validate_flake8_config(flake8_config):
        print("✓ Flake8 configuration created and validated")
    else:
        print("✗ Failed to create Flake8 configuration")
        sys.exit(1)
    
    print("Linting and formatting tools setup complete!")

if __name__ == "__main__":
    main()