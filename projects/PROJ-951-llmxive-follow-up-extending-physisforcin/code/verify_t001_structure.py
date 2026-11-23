"""
Verification script for T001: Create project root directories.

This script verifies that the root directory structure was created correctly.
It provides a tree view of the created directories.
"""
import os
from pathlib import Path

def print_tree(root_path, prefix=""):
    """Print a tree view of the directory structure."""
    if not root_path.exists():
        print(f"{prefix}[MISSING] {root_path.name}/")
        return

    print(f"{prefix}[DIR] {root_path.name}/")
    
    try:
        entries = sorted(root_path.iterdir())
    except PermissionError:
        print(f"{prefix}  [PERMISSION DENIED]")
        return

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        current_prefix = "  " if prefix == "" else ("    " if prefix.endswith("[DIR]") else "  ")
        
        if entry.is_dir():
            print_tree(entry, prefix + ("└── " if is_last else "├── "))
        else:
            print(f"{prefix}{'└── ' if is_last else '├── '}[FILE] {entry.name}")

def main():
    """Verify T001 directory structure."""
    target_path = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code")
    
    print(f"Verifying T001: {target_path.absolute()}")
    print("=" * 60)
    
    if not target_path.exists():
        print("ERROR: Root directory does not exist. Run create_t001_root.py first.")
        return 1
    
    if not target_path.is_dir():
        print("ERROR: Path exists but is not a directory.")
        return 1
    
    print(f"Root directory exists: {target_path.absolute()}")
    print("Directory structure:")
    print("-" * 60)
    print_tree(target_path)
    print("-" * 60)
    print("SUCCESS: T001 verification passed.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
