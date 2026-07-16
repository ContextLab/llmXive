"""
Linting and formatting configuration management.

This module provides functions to retrieve and validate
Ruff and Black configuration settings for the project.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Try to import tomli for reading TOML, fallback to tomllib for Python 3.11+
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore


def get_ruff_config() -> Dict[str, Any]:
    """
    Retrieve the Ruff configuration for the project.
    
    Returns:
        Dict containing Ruff configuration settings.
    """
    return {
        "target-version": "py311",
        "line-length": 88,
        "select": [
            "E",      # pycodestyle errors
            "W",      # pycodestyle warnings
            "F",      # Pyflakes
            "I",      # isort
            "B",      # flake8-bugbear
            "C4",     # flake8-comprehensions
            "UP",     # pyupgrade
            "ARG",    # flake8-unused-arguments
            "SIM",    # flake8-simplify
        ],
        "ignore": [
            "E501",   # line too long (handled by black)
            "B008",   # do not perform function calls in argument defaults
            "ARG001", # unused arguments (sometimes needed for interface compatibility)
        ],
        "exclude": [
            ".git",
            "__pycache__",
            ".eggs",
            "*.egg-info",
            "build",
            "dist",
            "venv",
            ".venv",
        ],
    }


def get_black_config() -> Dict[str, Any]:
    """
    Retrieve the Black configuration for the project.
    
    Returns:
        Dict containing Black configuration settings.
    """
    return {
        "line-length": 88,
        "target-version": ["py311"],
        "skip-string-normalization": False,
        "exclude": r"""
        (
            __pycache__
            | .git
            | .eggs
            | \.egg-info
            | build
            | dist
            | venv
            | \.venv
        )
        """,
    }


def validate_linting_setup(project_root: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Validate that the linting and formatting tools are properly configured.
    
    Checks for:
    1. Presence of configuration files (pyproject.toml, .ruff.toml, etc.)
    2. Installation of required packages (ruff, black)
    
    Args:
        project_root: Path to the project root directory. Defaults to current directory.
        
    Returns:
        Tuple of (is_valid, message)
    """
    if project_root is None:
        project_root = Path.cwd()
    
    issues = []
    
    # Check if ruff is installed
    try:
        import ruff  # type: ignore
    except ImportError:
        issues.append("ruff is not installed. Run: pip install ruff")
    
    # Check if black is installed
    try:
        import black  # type: ignore
    except ImportError:
        issues.append("black is not installed. Run: pip install black")
    
    # Check for configuration files
    config_files = [
        project_root / "pyproject.toml",
        project_root / ".ruff.toml",
        project_root / ".ruff_cache",
        project_root / "setup.cfg",
    ]
    
    has_config = any(f.exists() for f in config_files if f.suffix in [".toml", ".cfg"])
    
    if not has_config:
        issues.append(
            "No linting configuration file found. "
            "Create pyproject.toml with [tool.ruff] and [tool.black] sections, "
            "or use .ruff.toml and .black.toml."
        )
    
    if issues:
        return False, "; ".join(issues)
    
    return True, "Linting and formatting tools are properly configured."


def main() -> None:
    """Main entry point for linting configuration validation."""
    print("Validating linting and formatting setup...")
    
    is_valid, message = validate_linting_setup()
    print(message)
    
    if not is_valid:
        sys.exit(1)
    
    # Display current configurations
    print("\nCurrent Ruff configuration:")
    ruff_config = get_ruff_config()
    for key, value in ruff_config.items():
        print(f"  {key}: {value}")
    
    print("\nCurrent Black configuration:")
    black_config = get_black_config()
    for key, value in black_config.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
