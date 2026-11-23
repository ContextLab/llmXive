"""
Runner script to execute the complete T001 setup sequence.

Executes T001 (root), T001b (base), and T001c (detailed structure) in order.
"""
import sys
from pathlib import Path

# Import task runners
from create_t001_root import main as t001_main
from create_t001b_directories import main as t001b_main
from create_t001c_structure import main as t001c_main

def main():
    """Execute the complete T001 setup sequence."""
    print("=" * 60)
    print("Starting T001 Setup Sequence")
    print("=" * 60)
    
    # Step 1: Create project root directories
    print("\n[Step 1/3] Executing T001: Create project root directories...")
    exit_code = t001_main()
    if exit_code != 0:
        print("T001 failed. Aborting sequence.")
        return exit_code
    print("T001 completed successfully.")
    
    # Step 2: Create base directories
    print("\n[Step 2/3] Executing T001b: Create src/, tests/, data/...")
    exit_code = t001b_main()
    if exit_code != 0:
        print("T001b failed. Aborting sequence.")
        return exit_code
    print("T001b completed successfully.")
    
    # Step 3: Create detailed module structure
    print("\n[Step 3/3] Executing T001c: Create specific module directories...")
    exit_code = t001c_main()
    if exit_code != 0:
        print("T001c failed. Aborting sequence.")
        return exit_code
    print("T001c completed successfully.")
    
    print("\n" + "=" * 60)
    print("T001 Setup Sequence completed successfully!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())