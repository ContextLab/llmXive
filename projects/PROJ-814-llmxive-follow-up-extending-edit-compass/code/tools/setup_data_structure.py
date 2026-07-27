import os
import sys
from pathlib import Path

def main():
    """
    Setup the required data directory structure for the llmXive project.
    Creates: data/raw/, data/filtered/, data/scores/, outputs/
    """
    # Define the project root (assuming this script is in code/tools/)
    # We need to go up two levels to reach the project root where 'data' and 'outputs' reside
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent

    data_dirs = [
        "data/raw",
        "data/filtered",
        "data/scores",
    ]
    
    output_dirs = [
        "outputs",
    ]

    all_dirs = data_dirs + output_dirs

    created = []
    for dir_path in all_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    if not created:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {len(created)} directories.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())