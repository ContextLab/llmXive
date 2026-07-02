"""
Script to create the required directory structure for the project.
This script ensures all necessary directories for code, data, output, and tests exist.
"""
import os
import sys

def create_directories():
    """Create the project directory structure."""
    # Define the base paths relative to the project root
    base_dirs = [
        "code",
        "code/data",
        "code/data/raw",
        "code/data/processed",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "output",
        "output/plots"
    ]

    created = []
    skipped = []

    for dir_path in base_dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            if os.path.isdir(dir_path):
                created.append(dir_path)
        except Exception as e:
            print(f"Error creating {dir_path}: {e}", file=sys.stderr)
            skipped.append(dir_path)

    print(f"Directory structure setup complete.")
    print(f"Created: {len(created)} directories")
    if skipped:
        print(f"Skipped/Failed: {len(skipped)} directories")
        for s in skipped:
            print(f"  - {s}")
    else:
        print("All directories created successfully.")

    return len(skipped) == 0

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
