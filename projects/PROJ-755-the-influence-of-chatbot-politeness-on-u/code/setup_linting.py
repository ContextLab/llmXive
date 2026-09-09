"""
Script to configure linting (ruff/flake8) and formatting (black) tools.
Creates configuration files and provides validation helpers.
"""
import os
import sys
import tomllib
import configparser
import argparse
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
RUFF_CONFIG_PATH = PROJECT_ROOT / "ruff.toml"
FLAKE8_CONFIG_PATH = PROJECT_ROOT / ".flake8"


def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and return status."""
    if path.exists():
        print(f"✓ {description} exists: {path}")
        return True
    print(f"✗ {description} missing: {path}")
    return False


def validate_ruff_config() -> bool:
    """Validate ruff configuration file."""
    if not check_file_exists(RUFF_CONFIG_PATH, "Ruff config"):
        return False
    try:
        # Ruff uses TOML
        with open(RUFF_CONFIG_PATH, "rb") as f:
            config = tomllib.load(f)
        if "lint" not in config and "select" not in config:
            print("⚠ Ruff config exists but may be incomplete (missing 'lint' or 'select')")
            return False
        print("✓ Ruff config is valid TOML and contains expected keys")
        return True
    except Exception as e:
        print(f"✗ Ruff config validation failed: {e}")
        return False


def validate_pyproject_black() -> bool:
    """Validate Black configuration in pyproject.toml."""
    if not check_file_exists(PYPROJECT_PATH, "pyproject.toml"):
        return False
    try:
        with open(PYPROJECT_PATH, "rb") as f:
            config = tomllib.load(f)
        if "tool" not in config or "black" not in config["tool"]:
            print("⚠ pyproject.toml exists but missing [tool.black] section")
            return False
        print("✓ Black config in pyproject.toml is valid")
        return True
    except Exception as e:
        print(f"✗ pyproject.toml validation failed: {e}")
        return False


def validate_flake8_config() -> bool:
    """Validate flake8 configuration file."""
    if not check_file_exists(FLAKE8_CONFIG_PATH, "Flake8 config"):
        return False
    try:
        config = configparser.ConfigParser()
        config.read(FLAKE8_CONFIG_PATH)
        if "flake8" not in config:
            print("⚠ Flake8 config exists but missing [flake8] section")
            return False
        print("✓ Flake8 config is valid and contains expected section")
        return True
    except Exception as e:
        print(f"✗ Flake8 config validation failed: {e}")
        return False


def create_ruff_config() -> None:
    """Create a default ruff.toml configuration."""
    content = """# Ruff configuration
[lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
    "C901", # too complex
]

[lint.isort]
known-first-party = ["code", "tests"]

[format]
# Black-compatible formatting
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    with open(RUFF_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {RUFF_CONFIG_PATH}")


def create_black_config() -> None:
    """Create Black configuration in pyproject.toml."""
    # Read existing pyproject.toml if it exists
    if PYPROJECT_PATH.exists():
        with open(PYPROJECT_PATH, "rb") as f:
            try:
                existing_config = tomllib.load(f)
            except Exception:
                existing_config = {}
    else:
        existing_config = {}

    # Ensure [tool] section exists
    if "tool" not in existing_config:
        existing_config["tool"] = {}

    # Set black config
    black_config = {
        "line-length": 88,
        "target-version": ["py39", "py310", "py311"],
        "skip-magic-trailing-comma": False,
    }
    existing_config["tool"]["black"] = black_config

    # Write back
    # Since tomllib is read-only, we write manually for simplicity
    with open(PYPROJECT_PATH, "w", encoding="utf-8") as f:
        f.write("# Project configuration\n")
        f.write("[build-system]\n")
        f.write('requires = ["setuptools>=45", "wheel"]\n')
        f.write('build-backend = "setuptools.build_meta"\n\n')
        f.write("[tool.black]\n")
        f.write("line-length = 88\n")
        f.write('target-version = ["py39", "py310", "py311"]\n')
        f.write("skip-magic-trailing-comma = false\n")
    print(f"Updated: {PYPROJECT_PATH} with [tool.black] section")


def create_flake8_config() -> None:
    """Create a default .flake8 configuration."""
    content = """[flake8]
max-line-length = 88
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    *.egg-info
ignore = E501,W503
"""
    with open(FLAKE8_CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {FLAKE8_CONFIG_PATH}")


def install_linting_tools() -> None:
    """Print installation instructions for linting tools."""
    print("\n--- Linting & Formatting Tools Installation ---")
    print("Run the following commands to install the tools:")
    print("  pip install ruff black flake8")
    print("\nTo format code:")
    print("  black code/ tests/")
    print("\nTo lint code:")
    print("  ruff check code/ tests/")
    print("  flake8 code/ tests/")


def main() -> None:
    """Main entry point for linting setup."""
    parser = argparse.ArgumentParser(description="Configure linting and formatting tools")
    parser.add_argument("--validate", action="store_true", help="Validate existing configs")
    parser.add_argument("--create", action="store_true", help="Create default configs")
    parser.add_argument("--install", action="store_true", help="Show installation instructions")
    args = parser.parse_args()

    if not any([args.validate, args.create, args.install]):
        # Default: create configs if missing
        args.create = True

    if args.create:
        print("Creating linting configuration files...")
        create_ruff_config()
        create_black_config()
        create_flake8_config()
        print("Configuration files created successfully.")

    if args.validate:
        print("Validating linting configuration files...")
        ruff_ok = validate_ruff_config()
        black_ok = validate_pyproject_black()
        flake8_ok = validate_flake8_config()
        if ruff_ok and black_ok and flake8_ok:
            print("All configurations valid.")
        else:
            print("Some configurations are missing or invalid.")
            sys.exit(1)

    if args.install:
        install_linting_tools()


if __name__ == "__main__":
    main()