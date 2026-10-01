"""
Verification script for task T001b: Initialize Python packages.
Ensures __init__.py files exist in all required package directories
and that the 'code' package is importable.
"""
import os
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    packages = [
        "code",
        "tests",
        "code/utils",
        "code/models"
    ]

    missing = []
    for pkg in packages:
        pkg_path = project_root / pkg
        init_file = pkg_path / "__init__.py"
        
        if not pkg_path.exists():
            missing.append(f"Directory missing: {pkg_path}")
        elif not init_file.exists():
            missing.append(f"__init__.py missing: {init_file}")

    if missing:
        for msg in missing:
            print(f"ERROR: {msg}", file=sys.stderr)
        print("Directory/Package initialization failed.", file=sys.stderr)
        sys.exit(1)

    # Verification: Ensure 'code' is importable
    try:
        # Add project root to path temporarily if not already there
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        import code
        print("Verification successful: 'code' package is importable.")
    except ImportError as e:
        print(f"ERROR: Failed to import 'code' package: {e}", file=sys.stderr)
        sys.exit(1)

    print("All package initializations verified.")
    sys.exit(0)

if __name__ == "__main__":
    main()