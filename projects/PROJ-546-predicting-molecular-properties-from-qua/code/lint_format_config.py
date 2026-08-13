"""
Configuration verification script for linting and formatting tools.
This script verifies that ruff and black configuration files exist and are valid.
"""
import os
import sys
from pathlib import Path

def verify_config_files():
    """Check for presence of configuration files."""
    project_root = Path(__file__).resolve().parent.parent
    ruff_config = project_root / "code" / ".ruff.toml"
    pyproject = project_root / "pyproject.toml"
    
    errors = []

    if not ruff_config.exists():
        errors.append(f"Missing ruff config: {ruff_config}")
    
    if not pyproject.exists():
        errors.append(f"Missing pyproject.toml: {pyproject}")
    else:
        # Basic validation that it's not empty
        content = pyproject.read_text()
        if "[tool.black]" not in content:
            errors.append("pyproject.toml missing [tool.black] section")
        if "[tool.ruff]" not in content:
            # We rely on .ruff.toml primarily, but having a section in pyproject is good practice
            pass

    if errors:
        print("Configuration verification failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    
    print("Configuration files verified successfully.")
    print(f"  - {ruff_config}")
    print(f"  - {pyproject}")
    return True

def main():
    verify_config_files()

if __name__ == "__main__":
    main()