"""
Verification script for T001a: Directory structure and file creation
Run this to confirm all required directories and files exist.
"""
import os
import sys
from pathlib import Path

def verify_structure():
    base = Path("projects/PROJ-367-the-influence-of-algorithmic-recommendat")
    required_dirs = [
        base / "code",
        base / "tests",
        base / "tests" / "unit",
        base / "tests" / "integration",
        base / "data" / "raw",
        base / "data" / "processed",
        base / "docs" / "reports",
    ]

    required_files = [
        base / "code" / "__init__.py",
        base / "tests" / "__init__.py",
        base / "tests" / "unit" / "__init__.py",
        base / "tests" / "integration" / "__init__.py",
        base / "code" / "requirements.txt",
        base / "pytest.ini",
        base / "pyproject.toml",
    ]

    errors = []

    for d in required_dirs:
        if not d.exists():
            errors.append(f"Missing directory: {d}")
        else:
            print(f"✓ Directory exists: {d}")

    for f in required_files:
        if not f.exists():
            errors.append(f"Missing file: {f}")
        else:
            print(f"✓ File exists: {f}")

    if errors:
        print("\n❌ Verification FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n✅ All required directories and files verified successfully.")
        sys.exit(0)

if __name__ == "__main__":
    verify_structure()