"""
Script to initialize the project directory structure for PROJ-164.
Implements Task T001a: Create project structure.
"""
import os
import sys

def main():
    # Define the directory structure relative to the project root
    # Assuming this script is run from the project root or the paths are relative to cwd
    # The task requires specific directories under the project root.
    
    # We assume the script is executed from the project root.
    # If run from elsewhere, we might need to adjust, but standard practice is root.
    base_dirs = [
        "code",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "models",
        "docs",
        "docs/contracts",
        "state/projects",
        "logs"  # Added for FR-008 logging infrastructure readiness
    ]

    created = 0
    skipped = 0

    print("Initializing project structure for PROJ-164...")
    
    for dir_path in base_dirs:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                print(f"Created directory: {dir_path}")
                created += 1
            else:
                # Check if it's actually a directory
                if os.path.isdir(dir_path):
                    print(f"Directory exists: {dir_path}")
                    skipped += 1
                else:
                    print(f"ERROR: Path exists but is not a directory: {dir_path}")
                    return 1
        except PermissionError:
            print(f"ERROR: Permission denied creating {dir_path}")
            return 1
        except Exception as e:
            print(f"ERROR: Failed to create {dir_path}: {e}")
            return 1

    print(f"\nProject structure initialization complete.")
    print(f"Directories created: {created}")
    print(f"Directories skipped (already exist): {skipped}")
    
    # Verify the critical paths exist
    required_paths = [
        "code/utils",
        "data/raw",
        "state/projects"
    ]
    
    for p in required_paths:
        if not os.path.isdir(p):
            print(f"CRITICAL ERROR: Required path {p} does not exist after setup.")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
