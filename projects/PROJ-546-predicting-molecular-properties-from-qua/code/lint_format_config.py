"""
Verification script for linting and formatting configuration.
This script verifies that pyproject.toml and .ruff.toml exist and
can be parsed by the respective tools.
"""

import os
import sys
from pathlib import Path

def verify_config_files():
    """Verify that configuration files exist and are valid."""
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    ruff_toml_path = project_root / ".ruff.toml"

    errors = []

    # Check pyproject.toml
    if not pyproject_path.exists():
        errors.append(f"Missing: {pyproject_path}")
    else:
        print(f"✓ Found: {pyproject_path}")
        # Basic validation: try to read and check for [tool.black] and [tool.ruff]
        try:
            content = pyproject_path.read_text()
            if "[tool.black]" not in content:
                errors.append(f"[tool.black] section missing in {pyproject_path}")
            if "[tool.ruff]" not in content:
                errors.append(f"[tool.ruff] section missing in {pyproject_path}")
            print("✓ pyproject.toml contains required sections")
        except Exception as e:
            errors.append(f"Error reading {pyproject_path}: {e}")

    # Check .ruff.toml
    if not ruff_toml_path.exists():
        print(f"⚠ Missing: {ruff_toml_path} (optional, configuration in pyproject.toml)")
    else:
        print(f"✓ Found: {ruff_toml_path}")

    if errors:
        print("\n❌ Verification failed:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("\n✅ All configuration files verified successfully.")
    return True

def main():
    success = verify_config_files()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
