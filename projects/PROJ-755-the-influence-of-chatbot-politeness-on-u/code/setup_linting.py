"""
Setup script for linting and formatting tools.
Validates configuration files for Ruff, Black, and Flake8.
"""
import os
import sys
from pathlib import Path
import tomllib
import configparser
import argparse

def check_file_exists(filepath: str) -> bool:
    """Check if a configuration file exists."""
    return Path(filepath).exists()

def validate_ruff_config() -> bool:
    """Validate .ruff.toml configuration."""
    config_path = Path(".ruff.toml")
    if not config_path.exists():
        print("Error: .ruff.toml not found.")
        return False
    
    try:
        # Basic validation: ensure it's valid TOML
        with open(config_path, "rb") as f:
            tomllib.load(f)
        print("✓ .ruff.toml is valid TOML.")
        return True
    except Exception as e:
        print(f"Error: .ruff.toml is invalid TOML: {e}")
        return False

def validate_pyproject_black() -> bool:
    """Validate Black configuration in pyproject.toml."""
    config_path = Path("pyproject.toml")
    if not config_path.exists():
        print("Error: pyproject.toml not found.")
        return False

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        
        if "tool" not in data or "black" not in data["tool"]:
            print("Warning: Black configuration missing in pyproject.toml.")
            return False
        
        print("✓ Black configuration found in pyproject.toml.")
        return True
    except Exception as e:
        print(f"Error: Invalid pyproject.toml: {e}")
        return False

def validate_flake8() -> bool:
    """Validate .flake8 configuration."""
    config_path = Path(".flake8")
    if not config_path.exists():
        print("Warning: .flake8 not found (Ruff is preferred, but .flake8 is acceptable).")
        return True  # Not critical if Ruff is used

    try:
        config = configparser.ConfigParser()
        config.read(config_path)
        
        if "flake8" not in config:
            print("Warning: [flake8] section missing in .flake8.")
            return False
        
        print("✓ .flake8 configuration found.")
        return True
    except Exception as e:
        print(f"Error: Invalid .flake8: {e}")
        return False

def main():
    """Run validation checks for linting and formatting tools."""
    parser = argparse.ArgumentParser(description="Validate linting and formatting configurations.")
    parser.add_argument("--strict", action="store_true", help="Fail if any config is missing.")
    args = parser.parse_args()

    results = []

    print("Validating linting and formatting configurations...")
    print("-" * 50)

    # Check Ruff
    ruff_valid = validate_ruff_config()
    results.append(("Ruff", ruff_valid))

    # Check Black
    black_valid = validate_pyproject_black()
    results.append(("Black", black_valid))

    # Check Flake8
    flake8_valid = validate_flake8()
    results.append(("Flake8", flake8_valid))

    print("-" * 50)
    all_valid = all(valid for _, valid in results)

    if all_valid:
        print("✓ All configurations are valid.")
        return 0
    else:
        print("✗ Some configurations are invalid or missing.")
        for name, valid in results:
            status = "✓" if valid else "✗"
            print(f"  {status} {name}")
        
        if args.strict:
            return 1
        return 0

if __name__ == "__main__":
    sys.exit(main())