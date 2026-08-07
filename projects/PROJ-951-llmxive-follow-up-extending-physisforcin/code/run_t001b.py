import os
import sys
from pathlib import Path
from create_t001b_directories import create_t001b_directories
from verify_t001b_structure import verify_t001b_structure

def main():
    """
    Orchestrates the creation and verification of T001b directories.
    """
    # Determine project root (code directory)
    if len(sys.argv) > 1:
        code_root = Path(sys.argv[1])
    else:
        code_root = Path.cwd()

    print(f"Running T001b Task on: {code_root}")
    print("=" * 50)

    # Step 1: Create Directories
    print("Step 1: Creating directories...")
    create_t001b_directories(code_root)

    # Step 2: Verify Directories
    print("\nStep 2: Verifying structure...")
    success = verify_t001b_structure(code_root)

    if success:
        print("\nT001b Task Completed Successfully.")
        return 0
    else:
        print("\nT001b Task Failed Verification.")
        return 1

if __name__ == "__main__":
    sys.exit(main())