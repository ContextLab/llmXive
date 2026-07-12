"""
Linting and formatting configuration for llmXive project.

This module provides centralized configuration for flake8 and black,
ensuring consistent code style across the project.
"""

import os
import subprocess
import sys
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Black configuration
BLACK_CONFIG = {
    "line_length": 88,
    "target_version": ["py311"],
    "include": r"\.pyi?$",
    "exclude": r"/(\.eggs|\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|_build|buck-out|build|dist)/",
}

# Flake8 configuration
FLAKE8_CONFIG = {
    "max-line-length": 88,
    "extend-ignore": [
        "E203",  # Whitespace before ':' (conflicts with black)
        "W503",  # Line break before binary operator (conflicts with black)
    ],
    "exclude": [
        ".eggs",
        ".git",
        ".mypy_cache",
        ".nox",
        ".tox",
        ".venv",
        "_build",
        "buck-out",
        "build",
        "dist",
        "venv",
    ],
    "per-file-ignores": {
        "__init__.py": "F401",  # Allow unused imports in __init__.py
    },
}

# Pylint configuration (optional, for more strict checking)
PYLINT_CONFIG = {
    "disable": [
        "C0114",  # missing-module-docstring
        "C0115",  # missing-class-docstring
        "C0116",  # missing-function-docstring
        "R0903",  # too-few-public-methods
        "W0511",  # TODO/FIXME comments
    ],
    "max-line-length": 88,
    "good-names": ["i", "j", "k", "ex", "Run", "_"],
}

def create_black_config_file():
    """Create a pyproject.toml with black configuration."""
    config_content = """[tool.black]
line-length = {line_length}
target-version = {target_version}
include = '{include}'
exclude = '{exclude}'
""".format(
        line_length=BLACK_CONFIG["line_length"],
        target_version=' = '.join(f'py{v}' for v in BLACK_CONFIG["target_version"]),
        include=BLACK_CONFIG["include"],
        exclude=BLACK_CONFIG["exclude"],
    )
    
    config_path = PROJECT_ROOT / "pyproject.toml"
    
    # Read existing content if file exists
    if config_path.exists():
        existing_content = config_path.read_text()
        if "[tool.black]" in existing_content:
            print("Black configuration already exists in pyproject.toml")
            return
        existing_content += "\n" + config_content
    else:
        existing_content = config_content
    
    config_path.write_text(existing_content)
    print(f"Created/updated black configuration in {config_path}")

def create_flake8_config_file():
    """Create a .flake8 configuration file."""
    config_content = """[flake8]
max-line-length = {max_line_length}
extend-ignore = {extend_ignore}
exclude = {exclude}
per-file-ignores = {per_file_ignores}
""".format(
        max_line_length=FLAKE8_CONFIG["max-line-length"],
        extend_ignore=", ".join(FLAKE8_CONFIG["extend-ignore"]),
        exclude=", ".join(FLAKE8_CONFIG["exclude"]),
        per_file_ignores="; ".join(
            f"{k}:{v}" for k, v in FLAKE8_CONFIG["per-file-ignores"].items()
        ),
    )
    
    config_path = PROJECT_ROOT / ".flake8"
    config_path.write_text(config_content)
    print(f"Created flake8 configuration in {config_path}")

def run_black_check(path=None, fix=False):
    """Run black to check or fix formatting."""
    cmd = ["black", "--check"] if not fix else ["black"]
    
    if path:
        cmd.append(str(path))
    else:
        cmd.append("code")
        cmd.append("tests")
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode == 0

def run_flake8_check(path=None):
    """Run flake8 to check for linting issues."""
    cmd = ["flake8"]
    
    if path:
        cmd.append(str(path))
    else:
        cmd.append("code")
        cmd.append("tests")
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode == 0

def setup_linting():
    """Set up all linting and formatting configuration files."""
    print("Setting up linting and formatting tools...")
    
    # Create configuration files
    create_black_config_file()
    create_flake8_config_file()
    
    # Check if tools are installed
    try:
        subprocess.run(["black", "--version"], capture_output=True, check=True)
        print("✓ Black is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Black is not installed. Install with: pip install black")
    
    try:
        subprocess.run(["flake8", "--version"], capture_output=True, check=True)
        print("✓ Flake8 is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠ Flake8 is not installed. Install with: pip install flake8")
    
    print("\nTo run linting checks:")
    print("  python code/linting_config.py --check")
    print("\nTo fix formatting issues:")
    print("  python code/linting_config.py --fix")

def main():
    """Main entry point for linting configuration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Configure and run linting tools")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Set up linting configuration files",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run linting checks (black --check, flake8)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix formatting issues with black",
    )
    parser.add_argument(
        "--path",
        type=str,
        help="Specific path to check/fix (default: code and tests directories)",
    )
    
    args = parser.parse_args()
    
    if args.setup:
        setup_linting()
    elif args.check:
        print("Running linting checks...")
        black_ok = run_black_check(args.path)
        flake8_ok = run_flake8_check(args.path)
        
        if black_ok and flake8_ok:
            print("✓ All checks passed!")
            sys.exit(0)
        else:
            if not black_ok:
                print("✗ Black checks failed")
            if not flake8_ok:
                print("✗ Flake8 checks failed")
            sys.exit(1)
    elif args.fix:
        print("Fixing formatting issues...")
        success = run_black_check(args.path, fix=True)
        if success:
            print("✓ Formatting fixed!")
            sys.exit(0)
        else:
            print("✗ Failed to fix formatting")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()