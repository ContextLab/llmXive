"""
Linting and formatting configuration for the project.

This module provides configuration for Ruff (linter) and Black (formatter).
It acts as a single source of truth for tool settings to ensure consistency.
"""
import tomli_w
import tomli
from pathlib import Path
import os
from typing import Dict, Any

# Default configuration for Ruff (linter)
RUFF_CONFIG = {
    "lint": {
        "select": [
            "E",  # pycodestyle errors
            "W",  # pycodestyle warnings
            "F",  # Pyflakes
            "I",  # isort
            "C",  # flake8-comprehensions
            "B",  # flake8-bugbear
            "UP", # pyupgrade
            "SIM",# flake8-simplify
        ],
        "ignore": [
            "E501", # Line too long (handled by Black)
            "B008", # Do not perform function call in argument defaults (common in dataclasses)
        ],
        "extend-per-file-ignores": {
            "tests/*": ["S101"], # Allow assert in tests
            "code/src/utils/config.py": ["E501"] # Config files often have long lines
        },
        "isort": {
            "known-first-party": ["src", "tests", "utils"],
            "force-single-line": True,
        },
        "pyupgrade": {
            "keep-runtime-typing": False,
        },
    },
    "line-length": 88,
    "target-version": "py311",
}

# Default configuration for Black (formatter)
BLACK_CONFIG = {
    "line-length": 88,
    "target-version": ["py311"],
    "include": r"\.pyi?$",
    "exclude": r"""
        /(
            \.git
          | \.hg
          | \.mypy_cache
          | \.tox
          | \.venv
          | _build
          | buck-out
          | build
          | dist
        )/
    """,
}

def get_ruff_config() -> Dict[str, Any]:
    """Return the Ruff configuration dictionary."""
    return RUFF_CONFIG

def get_black_config() -> Dict[str, Any]:
    """Return the Black configuration dictionary."""
    return BLACK_CONFIG

def write_pyproject_toml(project_root: Path) -> None:
    """
    Write the linting and formatting configuration to pyproject.toml.
    
    Args:
        project_root: The root directory of the project.
    """
    pyproject_path = project_root / "pyproject.toml"
    
    # Load existing pyproject.toml if it exists
    existing_config = {}
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                existing_config = tomli.load(f)
        except Exception:
            # If parsing fails, start fresh
            existing_config = {}
    
    # Ensure tool sections exist
    if "tool" not in existing_config:
        existing_config["tool"] = {}
    
    # Update with our configurations
    existing_config["tool"]["ruff"] = RUFF_CONFIG
    existing_config["tool"]["black"] = BLACK_CONFIG
    
    # Write back
    with open(pyproject_path, "wb") as f:
        tomli_w.dump(existing_config, f)
    
    print(f"Updated {pyproject_path} with Ruff and Black configuration.")

def create_ruff_toml(project_root: Path) -> None:
    """
    Create a standalone .ruff.toml file (alternative to pyproject.toml).
    
    Args:
        project_root: The root directory of the project.
    """
    ruff_toml_path = project_root / ".ruff.toml"
    
    with open(ruff_toml_path, "w") as f:
        # Simple TOML serialization for .ruff.toml
        f.write("# Ruff configuration\n")
        f.write(f'line-length = {RUFF_CONFIG["line-length"]}\n')
        f.write(f'target-version = "{RUFF_CONFIG["target-version"]}"\n\n')
        
        f.write("[lint]\n")
        selects = ", ".join([f'"{s}"' for s in RUFF_CONFIG["lint"]["select"]])
        f.write(f'select = [{selects}]\n')
        
        ignores = ", ".join([f'"{i}"' for i in RUFF_CONFIG["lint"]["ignore"]])
        f.write(f'ignore = [{ignores}]\n')
        
        f.write(f'target-version = "{RUFF_CONFIG["target-version"]}"\n')
    
    print(f"Created {ruff_toml_path} with Ruff configuration.")

def main() -> None:
    """Main entry point to configure linting tools."""
    project_root = Path.cwd()
    print(f"Configuring linting tools for project at: {project_root}")
    
    # Write to pyproject.toml (preferred method)
    write_pyproject_toml(project_root)
    
    # Optionally create .ruff.toml as well for explicit ruff configuration
    create_ruff_toml(project_root)
    
    print("Linting configuration complete.")
    print("\nNext steps:")
    print("1. Install tools: pip install ruff black")
    print("2. Format code: black code/")
    print("3. Run linter: ruff check code/")
    print("4. Fix linting issues: ruff check --fix code/")

if __name__ == "__main__":
    main()
