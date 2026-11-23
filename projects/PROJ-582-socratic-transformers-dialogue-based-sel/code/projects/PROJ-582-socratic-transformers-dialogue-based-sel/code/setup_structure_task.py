"""
Task T001a: Create project code structure.

This script creates the required directory structure for the Socratic Transformers
project under the specified project root.

Verification:
  Run `python code/projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/setup_structure_task.py`
  and then `ls -R projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src`
  to assert all directories exist.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to the script location or current working directory
# The task specifies paths relative to the project root.
# We assume the script is run from the repository root or the path is absolute.
# Based on the task description, the paths are:
# projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/...

# We will construct the base path assuming the script is in the code directory
# or we can use a fixed relative path from the project root.
# To be safe and portable, we define the target root relative to the current working directory.
PROJECT_ROOT = Path("projects/PROJ-582-socratic-transformers-dialogue-based-sel/code")
SRC_ROOT = PROJECT_ROOT / "src"

# Directories to create
required_dirs = [
    SRC_ROOT,
    SRC_ROOT / "data",
    SRC_ROOT / "train",
    SRC_ROOT / "eval",
    SRC_ROOT / "utils",
]

def create_directories():
    """Create all required directories if they do not exist."""
    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    if created_count > 0:
        print(f"Successfully created {created_count} new directories.")
    else:
        print("No new directories were created; all required directories already exist.")

def verify_structure():
    """Verify that all required directories exist."""
    missing = []
    for dir_path in required_dirs:
        if not dir_path.exists():
            missing.append(str(dir_path))
    
    if missing:
        print(f"ERROR: The following directories are missing: {missing}")
        return False
    
    print("Verification successful: All required directories exist.")
    return True

def main():
    """Main entry point for the script."""
    print(f"Target project root: {PROJECT_ROOT.resolve()}")
    create_directories()
    if verify_structure():
        # Print the recursive listing as verification evidence
        print("\n--- Directory Listing (Verification) ---")
        # We use os.walk to mimic 'ls -R' behavior for the src root
        for root, dirs, files in os.walk(SRC_ROOT):
            level = root.replace(str(SRC_ROOT), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            sub_indent = ' ' * 2 * (level + 1)
            for file in files:
                print(f'{sub_indent}{file}')
            for dir in dirs:
                print(f'{sub_indent}{dir}/')
        print("--- End Listing ---")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()