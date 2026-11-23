"""
Runner script for Task T001c.

Executes the directory creation logic defined in create_t001c_structure.py.
"""
import sys
from pathlib import Path
from create_t001c_structure import main as t001c_main

def main():
    """Execute T001c directory creation."""
    print("Running Task T001c: Create specific module directories...")
    exit_code = t001c_main()
    if exit_code == 0:
        print("T001c completed successfully.")
    else:
        print("T001c failed.")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
