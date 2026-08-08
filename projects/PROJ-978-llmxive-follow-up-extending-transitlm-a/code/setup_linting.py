"""
Setup script to initialize linting and formatting configuration.
This task (T003) ensures Ruff and Black are configured via pyproject.toml
and .ruff.toml. This script verifies the presence of these files.
"""
import os
import sys
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """Check if a file exists relative to the project root."""
    return Path(filepath).exists()


def check_config_content(filepath: str) -> bool:
    """Check if the configuration file contains expected content."""
    path = Path(filepath)
    if not path.exists():
        return False
    content = path.read_text()
    # Basic checks for Black and Ruff configuration
    if "black" in filepath.lower():
        return "line-length" in content and "target-version" in content
    if "ruff" in filepath.lower() or "pyproject" in filepath.lower():
        return "line-length" in content or "select" in content
    return True


def main():
    """Main entry point for setup_linting."""
    print("Checking linting and formatting configuration...")
    root = Path(__file__).parent

    files_to_check = [
        root / "pyproject.toml",
        root / ".ruff.toml",
    ]

    all_ok = True
    for f in files_to_check:
        rel_path = f.relative_to(root)
        if not check_file_exists(str(f)):
            print(f"FAIL: {rel_path} does not exist.")
            all_ok = False
        elif not check_config_content(str(f)):
            print(f"FAIL: {rel_path} exists but lacks expected configuration.")
            all_ok = False
        else:
            print(f"OK: {rel_path} is present and valid.")

    if all_ok:
        print("Linting and formatting configuration is complete.")
        sys.exit(0)
    else:
        print("Configuration check failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
