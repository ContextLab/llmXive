import os
import sys
from pathlib import Path

def main():
    """
    Create the code/tests/ directory at the repository root.
    This script ensures the directory exists for unit and integration tests.
    """
    project_root = Path(__file__).resolve().parent.parent
    test_dir = project_root / "code" / "tests"

    if not test_dir.exists():
        test_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {test_dir}")
    else:
        print(f"Directory already exists: {test_dir}")

    # Create a placeholder __init__.py to make it a package
    init_file = test_dir / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        print(f"Created placeholder file: {init_file}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
