"""
T001a: Create project code structure.

Creates the required directory tree for the Socratic Transformers project
under projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/.

Directories created:
- src/
- src/data/
- src/train/
- src/eval/
- src/utils/
"""
import os
import sys
from pathlib import Path

# Define the project root relative to the script location
# The script is expected to be run from: projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR  # This is the 'code' directory

# Define the relative paths to create
SRC_DIRS = [
    "src",
    "src/data",
    "src/train",
    "src/eval",
    "src/utils",
]

def create_directories():
    """Create the directory structure if it doesn't exist."""
    created_count = 0
    for rel_path in SRC_DIRS:
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
    print("\n--- Verifying Directory Structure ---")
    src_root = PROJECT_ROOT / "src"
    
    if not src_root.exists():
        print(f"ERROR: Root src directory does not exist: {src_root}")
        return False

    # Check all required subdirectories
    required_subdirs = ["data", "train", "eval", "utils"]
    all_exist = True
    
    for subdir in required_subdirs:
        path = src_root / subdir
        if path.exists() and path.is_dir():
            print(f"OK: {path}")
        else:
            print(f"MISSING: {path}")
            all_exist = False

    # Print recursive listing as verification evidence
    print("\n--- Recursive Listing (ls -R) ---")
    # Simulating 'ls -R src'
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

    print_tree(src_root)
    
    return all_exist

def main():
    """Main entry point."""
    print(f"Running T001a: Creating project code structure in {PROJECT_ROOT}")
    
    created = create_directories()
    if created > 0:
        print(f"Successfully created {created} new directories.")
    
    is_valid = verify_structure()
    
    if is_valid:
        print("\n✓ Verification PASSED: All required directories exist.")
        sys.exit(0)
    else:
        print("\n✗ Verification FAILED: Some directories are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
