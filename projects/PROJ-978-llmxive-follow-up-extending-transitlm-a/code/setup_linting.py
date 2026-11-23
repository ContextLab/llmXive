"""
Setup script to verify and initialize linting (Ruff) and formatting (Black) tools.
This script checks for the existence of configuration files and provides
installation instructions if they are missing.
"""
import os
import sys
from pathlib import Path

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists in the project root."""
    path = Path(filepath)
    exists = path.exists()
    status = "✓" if exists else "✗"
    print(f"{status} {filepath}: {'Found' if exists else 'Missing'}")
    return exists

def check_config_content(filepath: str, required_keys: list[str]) -> bool:
    """Check if a configuration file contains required keys."""
    path = Path(filepath)
    if not path.exists():
        return False

    try:
        content = path.read_text()
        missing_keys = [key for key in required_keys if key not in content]
        if missing_keys:
            print(f"  ⚠ Missing keys in {filepath}: {missing_keys}")
            return False
        return True
    except Exception as e:
        print(f"  ✗ Error reading {filepath}: {e}")
        return False

def main():
    """Main entry point for linting setup verification."""
    print("=== Linting & Formatting Setup Verification ===\n")

    # Check configuration files
    files_to_check = [
        "pyproject.toml",
        ".pre-commit-config.yaml",
    ]

    all_found = True
    for f in files_to_check:
        if not check_file_exists(f):
            all_found = False

    # Validate pyproject.toml content
    if Path("pyproject.toml").exists():
        print("\nValidating pyproject.toml content:")
        has_black = check_config_content(
            "pyproject.toml",
            ["[tool.black]", "line-length", "target-version"]
        )
        has_ruff = check_config_content(
            "pyproject.toml",
            ["[tool.ruff]", "select", "ignore"]
        )

        if not (has_black and has_ruff):
            all_found = False
            print("  ⚠ pyproject.toml is missing Black or Ruff configuration sections.")

    # Validate pre-commit config
    if Path(".pre-commit-config.yaml").exists():
        print("\nValidating .pre-commit-config.yaml content:")
        has_precommit = check_config_content(
            ".pre-commit-config.yaml",
            ["black", "ruff"]
        )
        if not has_precommit:
            all_found = False
            print("  ⚠ .pre-commit-config.yaml is missing Black or Ruff hooks.")

    print("\n" + "=" * 40)
    if all_found:
        print("✓ All linting and formatting configurations are present and valid.")
        print("\nNext steps:")
        print("  1. Install pre-commit: pip install pre-commit")
        print("  2. Install hooks: pre-commit install")
        print("  3. Run pre-commit: pre-commit run --all-files")
        return 0
    else:
        print("✗ Some configurations are missing or invalid.")
        print("\nPlease ensure 'pyproject.toml' and '.pre-commit-config.yaml' are created.")
        print("Refer to the project documentation for configuration templates.")
        return 1

if __name__ == "__main__":
    sys.exit(main())