"""
Script to initialize the project directory structure for PROJ-317.
Creates all necessary directories for data, code, tests, and documentation.
"""
import os
import sys

def main():
    # Define the base directory for the project
    # The script is run from the project root: projects/PROJ-317-...
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Relative paths to create
    paths = [
        "data/stimuli",
        "data/stimuli_metadata",
        "data/responses",
        "data/processed",
        "data/ethics",
        "code/data",
        "code/stimuli",
        "code/participants",
        "code/analysis",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "docs/ethics",
    ]

    created_count = 0
    skipped_count = 0

    for rel_path in paths:
        full_path = os.path.join(base_dir, rel_path)
        if os.path.exists(full_path):
            skipped_count += 1
        else:
            os.makedirs(full_path, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")

    print(f"\nProject structure initialization complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories already existing: {skipped_count}")

    return 0

if __name__ == "__main__":
    sys.exit(main())