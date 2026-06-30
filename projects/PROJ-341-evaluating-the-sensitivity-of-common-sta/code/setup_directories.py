"""
Setup script to create the project directory structure for llmXive PROJ-341.
This script ensures all required directories exist for data, code, tests, and reports.
"""
import os
import sys

def create_directories():
    """Create the project directory structure."""
    # Define the root directories relative to the project root
    # We assume this script is run from the project root or calculate based on script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    directories = [
        "code",
        "data",
        "tests",
        "data/raw",
        "data/simulation",
        "data/visualization",
        "data/reports"
    ]
    
    created = []
    skipped = []
    
    for dir_path in directories:
        full_path = os.path.join(project_root, dir_path)
        try:
            os.makedirs(full_path, exist_ok=True)
            # Verify it exists and is a directory
            if os.path.isdir(full_path):
                created.append(dir_path)
            else:
                print(f"Warning: {dir_path} exists but is not a directory.")
        except PermissionError:
            print(f"Error: Permission denied creating {dir_path}")
            return False
        except OSError as e:
            print(f"Error creating {dir_path}: {e}")
            return False
    
    print(f"Successfully created {len(created)} directories:")
    for d in created:
        print(f"  - {d}")
    
    if skipped:
        print(f"Skipped (already existed): {len(skipped)} directories")
        for d in skipped:
            print(f"  - {d}")
    
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
