import os
import sys

def main():
    """
    Create the required directory structure for PROJ-160.
    This script ensures that `code/`, `data/raw/`, `data/processed/`, `tests/`, and `contracts/`
    exist inside the project root.
    """
    # Determine project root based on this script's location
    # Assuming this script is in: projects/PROJ-160-investigating-the-impact-of-early-life-s/scripts/setup_dirs.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    required_dirs = [
        os.path.join(project_root, "code"),
        os.path.join(project_root, "data", "raw"),
        os.path.join(project_root, "data", "processed"),
        os.path.join(project_root, "tests"),
        os.path.join(project_root, "contracts"),
    ]

    created = []
    for d in required_dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            created.append(d)
            print(f"Created directory: {d}")
        else:
            print(f"Directory already exists: {d}")

    if not created:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {len(created)} directories.")

    return 0

if __name__ == "__main__":
    sys.exit(main())