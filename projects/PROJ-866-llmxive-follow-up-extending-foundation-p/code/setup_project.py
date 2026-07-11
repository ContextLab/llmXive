"""
Script to initialize the project directory structure.
Creates the required folders and empty __init__.py files.
"""
import os
import sys

def create_structure():
    """Create the project directory structure."""
    root_dirs = [
        "code",
        "data",
        "tests",
        "state",
        "data/raw",
        "data/processed",
        "data/results",
        "specs",
        "contracts"
    ]

    created = []
    for directory in root_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            created.append(directory)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory exists: {directory}")

    # Ensure __init__.py files exist for Python packages
    init_dirs = ["code", "data", "tests", "state"]
    for directory in init_dirs:
        init_path = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write('"""\n' + directory.title() + ' module\n"""\n')
            created.append(init_path)
            print(f"Created package init: {init_path}")

    return created

if __name__ == "__main__":
    print("Initializing llmXive project structure...")
    created_items = create_structure()
    if created_items:
        print(f"\nSuccess. Created {len(created_items)} items.")
    else:
        print("\nNo new items created (structure already exists).")
        sys.exit(0)
