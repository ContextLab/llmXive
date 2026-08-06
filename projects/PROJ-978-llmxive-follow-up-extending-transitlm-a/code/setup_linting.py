"""
Script to verify and initialize linting and formatting configurations.
This script ensures that ruff and black are configured correctly.
It does not run the tools but verifies the configuration files exist.
"""

import os
import sys
from pathlib import Path

def check_file_exists(path_str: str) -> bool:
    """Check if a file exists relative to the project root."""
    path = Path(path_str)
    if not path.exists():
        print(f"MISSING: {path_str}")
        return False
    print(f"FOUND: {path_str}")
    return True

def check_config_content(path_str: str, required_keys: list[str]) -> bool:
    """Check if a config file contains required keys."""
    path = Path(path_str)
    if not path.exists():
        return False
    
    content = path.read_text()
    missing = []
    for key in required_keys:
        if key not in content:
            missing.append(key)
    
    if missing:
        print(f"INCOMPLETE: {path_str} missing keys: {missing}")
        return False
    
    print(f"VALID: {path_str} contains required configuration")
    return True

def main():
    """Main entry point for setup verification."""
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print("Checking Linting and Formatting Configuration...")
    print("-" * 50)

    checks_passed = True

    # Check pyproject.toml
    if not check_file_exists("pyproject.toml"):
        checks_passed = False
    else:
        if not check_config_content("pyproject.toml", ["[tool.black]", "[tool.ruff]"]):
            checks_passed = False

    # Check .ruff.toml (optional but good practice)
    # We don't fail if missing if pyproject.toml has it, but we check for presence
    check_file_exists(".ruff.toml")

    # Check if tools are installed (optional runtime check)
    try:
        import black
        import ruff
        print("INFO: black and ruff packages are installed.")
    except ImportError as e:
        print(f"WARNING: Linting tools not installed: {e}")
        print("INFO: Run 'pip install black ruff' to install.")

    print("-" * 50)
    if checks_passed:
        print("SUCCESS: Linting and formatting configuration is complete.")
        return 0
    else:
        print("FAILURE: Some configuration checks failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())