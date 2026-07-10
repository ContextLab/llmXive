"""
Script to initialize the project directory structure.
This script ensures that the required directories exist.
"""
import os
import sys

def main():
    """Create the standard project directories."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "tests",
        "tests/integration",
        "artifacts",
        "figures"
    ]

    created = []
    for dir_path in directories:
        full_path = os.path.join(root_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created.append(dir_path)
        else:
            print(f"Directory exists: {dir_path}")

    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All directories already exist.")
    
    # Create __init__.py files if missing
    for dir_path in ["code", "tests", "tests/integration"]:
        full_path = os.path.join(root_dir, dir_path, "__init__.py")
        if not os.path.exists(full_path):
            with open(full_path, 'w') as f:
                f.write('"""Auto-generated init file."""\n')
            print(f"Created __init__.py in {dir_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())