"""
T001c: Create project data structure.

Creates the required directory tree for data at the project root.
Note: T004 adds .gitkeep files to these directories.
"""
import os
import sys
from pathlib import Path

# The script is located in 'code/', but data dirs are at project root (parent of code/)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent 

DATA_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
]

def create_directories():
    """Create the directory structure if it doesn't exist."""
    created_count = 0
    for rel_path in DATA_DIRS:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")
    return created_count

def verify_structure():
    """Verify that all required directories exist and print the tree."""
    print("\n--- Verifying Data Directory Structure ---")
    data_root = PROJECT_ROOT / "data"
    
    if not data_root.exists():
        print(f"ERROR: Root data directory does not exist: {data_root}")
        return False

    required_subdirs = ["raw", "processed", "results"]
    all_exist = True
    
    for subdir in required_subdirs:
        path = data_root / subdir
        if path.exists() and path.is_dir():
            print(f"OK: {path}")
        else:
            print(f"MISSING: {path}")
            all_exist = False

    # Print recursive listing
    print("\n--- Recursive Listing (ls -R data) ---")
    def print_tree(directory, prefix=""):
        print(f"{directory.name}/")
        try:
            entries = sorted(directory.iterdir())
            for i, entry in enumerate(entries):
                is_last = i == len(entries) - 1
                connector = "└── " if is_last else "├── "
                print(f"{prefix}{connector}{entry.name}")
                if entry.is_dir():
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    print_tree(entry, new_prefix)
        except PermissionError:
            print(f"{prefix}    [Permission Denied]")

    print_tree(data_root)
    
    return all_exist

def main():
    """Main entry point."""
    print(f"Running T001c: Creating data structure in {PROJECT_ROOT}")
    
    created = create_directories()
    if created > 0:
        print(f"Successfully created {created} new directories.")
    
    is_valid = verify_structure()
    
    if is_valid:
        print("\n✓ Verification PASSED: All required data directories exist.")
        sys.exit(0)
    else:
        print("\n✗ Verification FAILED: Some directories are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()