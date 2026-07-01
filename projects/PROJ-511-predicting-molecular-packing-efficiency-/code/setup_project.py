"""
Script to initialize the project directory structure for PROJ-511.
Creates standard folders for code, data, models, results, contracts, and specs.
"""
import os
import sys

def create_directories():
    """Create the required project directory structure."""
    # Define directories relative to the project root
    # The script assumes it is run from the project root
    base_dirs = [
        "code",
        "data",
        "data/raw_cif",
        "models",
        "results",
        "contracts",
        "specs"
    ]

    created = []
    skipped = []

    for dir_path in base_dirs:
        full_path = os.path.join(os.getcwd(), dir_path)
        try:
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
                created.append(dir_path)
            else:
                skipped.append(dir_path)
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)

    print("Directory structure setup complete.")
    if created:
        print(f"Created directories: {', '.join(created)}")
    if skipped:
        print(f"Already existed: {', '.join(skipped)}")

if __name__ == "__main__":
    create_directories()