"""
Setup script to verify and initialize linting and formatting tools.
This script checks for the presence of configuration files and
provides instructions if they are missing.
"""
import os
import sys
from pathlib import Path


def verify_config_files() -> bool:
    """
    Verify that linting (flake8) and formatting (black) configuration files exist.

    Returns:
        bool: True if all configuration files are present, False otherwise.
    """
    base_dir = Path(__file__).parent
    code_dir = base_dir / "code"

    # Ensure code directory exists
    code_dir.mkdir(parents=True, exist_ok=True)

    required_files = {
        ".flake8": "flake8 configuration",
        "pyproject.toml": "Black and other tool configuration",
        ".pre-commit-config.yaml": "Pre-commit hooks configuration"
    }

    missing_files = []

    for filename, description in required_files.items():
        file_path = code_dir / filename
        if not file_path.exists():
            missing_files.append((filename, description))
        else:
            print(f"✓ Found {filename} ({description})")

    if missing_files:
        print("\n⚠ Missing configuration files:")
        for filename, description in missing_files:
            print(f"  - {filename} ({description})")
        print("\nPlease create these files with appropriate configurations.")
        return False

    print("\n✓ All linting and formatting configuration files are present.")
    return True


def main() -> None:
    """Main entry point for the setup script."""
    print("Checking linting and formatting configuration...")
    success = verify_config_files()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
