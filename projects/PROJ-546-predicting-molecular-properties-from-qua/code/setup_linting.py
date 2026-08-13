"""
Script to verify and display the status of linting and formatting configurations.
This script ensures that .ruff.toml and pyproject.toml (for Black) are present
and readable.
"""
import os
import sys
from pathlib import Path

def check_file(path: Path) -> bool:
    if not path.exists():
        print(f"❌ Missing: {path}")
        return False
    if path.stat().st_size == 0:
        print(f"⚠️ Empty: {path}")
        return False
    print(f"✅ Found: {path} ({path.stat().st_size} bytes)")
    return True

def main():
    root = Path(__file__).parent
    ruff_config = root / ".ruff.toml"
    black_config = root / "pyproject.toml"
    reqs = root / "requirements.txt"

    print("Checking Linting and Formatting Configuration...")
    print("-" * 40)

    checks = [
        check_file(ruff_config),
        check_file(black_config),
        check_file(reqs),
    ]

    print("-" * 40)
    if all(checks):
        print("✅ All configuration files present and non-empty.")
        print("\nTo run linter:   ruff check .")
        print("To run formatter: black .")
        print("To check format:  black --check .")
        return 0
    else:
        print("❌ Some configuration files are missing or empty.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
