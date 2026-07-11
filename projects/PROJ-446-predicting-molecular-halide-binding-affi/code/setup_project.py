import os
from pathlib import Path

def main():
    """
    Initialize project directories for the Molecular Halide Binding Affinity project.
    
    Creates the following directory structure under the project root:
    - data/
    - docs/
    
    This script is idempotent (safe to run multiple times).
    """
    # Determine project root (parent of code/ directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Directories to create relative to project root
    directories = [
        "data",
        "docs"
    ]

    created = []
    skipped = []

    for dir_name in directories:
        target_path = project_root / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            created.append(str(target_path))
            print(f"Created directory: {target_path}")
        else:
            skipped.append(str(target_path))
            print(f"Directory already exists: {target_path}")

    print(f"\nSetup complete. Created {len(created)} directories.")
    if skipped:
        print(f"Skipped {len(skipped)} existing directories.")

    return 0

if __name__ == "__main__":
    exit(main())