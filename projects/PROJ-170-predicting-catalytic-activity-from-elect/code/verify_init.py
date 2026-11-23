"""
Verification script for T001b: Initialize Python packages.
Ensures __init__.py files exist in all required package directories
and verifies that the 'code' package is importable.
"""
import os
import sys
from pathlib import Path

def main():
    """Verify package initialization for T001b."""
    project_root = Path(__file__).resolve().parent.parent
    packages = [
        project_root / "code",
        project_root / "tests",
        project_root / "code" / "utils",
        project_root / "code" / "models",
    ]

    all_present = True
    for pkg in packages:
        init_file = pkg / "__init__.py"
        if not init_file.exists():
            print(f"ERROR: Missing __init__.py at {init_file}")
            all_present = False
        else:
            print(f"OK: Found {init_file}")

    if not all_present:
        print("FAILURE: Not all __init__.py files are present.")
        sys.exit(1)

    # Verification: Ensure importability
    try:
        # Add project root to path if not already there
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        import code
        print("OK: 'import code' succeeded.")
    except ImportError as e:
        print(f"FAILURE: 'import code' failed with error: {e}")
        sys.exit(1)

    print("T001b Verification: SUCCESS")

if __name__ == "__main__":
    main()