"""
Task T007: Setup directory structure for data and logs.

Creates the required directory hierarchy for the project:
- data/raw/
- data/processed/
- data/models/
- logs/

This script ensures that the necessary folders exist before data generation
or model training tasks are executed.
"""
import os
import sys

# Define the project root relative to this script's location
# Assuming this script is in code/, project root is parent of code/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the directories to create relative to the project root
DIRECTORIES_TO_CREATE = [
    os.path.join(PROJECT_ROOT, "data", "raw"),
    os.path.join(PROJECT_ROOT, "data", "processed"),
    os.path.join(PROJECT_ROOT, "data", "models"),
    os.path.join(PROJECT_ROOT, "logs"),
]

def setup_directories():
    """Create the required directory structure."""
    created_count = 0
    skipped_count = 0
    
    print(f"Setting up directories for project root: {PROJECT_ROOT}")
    
    for dir_path in DIRECTORIES_TO_CREATE:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"Created: {dir_path}")
                created_count += 1
            except OSError as e:
                print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            # exist_ok=True handles this, but explicit check for logging
            if os.path.isdir(dir_path):
                print(f"Directory exists: {dir_path}")
                skipped_count += 1
            else:
                print(f"Path exists but is not a directory: {dir_path}", file=sys.stderr)
                sys.exit(1)
    
    print(f"Setup complete. Created: {created_count}, Skipped: {skipped_count}")
    return True

def main():
    """Entry point for the script."""
    success = setup_directories()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()