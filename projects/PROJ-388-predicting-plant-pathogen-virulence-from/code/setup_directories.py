import os
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the project.
    Ensures all necessary folders exist relative to the project root.
    """
    # Define the project root (assuming this script is in code/ or root)
    # We will resolve paths relative to the script's location or current working directory
    # To be safe for the pipeline, we assume execution from the project root or that
    # paths are relative to the current working directory.
    
    base_dirs = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "output",
        "src/data",
        "src/analysis",
        "src/viz",
        "src/models",
        "src/utils"
    ]

    created = []
    for dir_path in base_dirs:
        p = Path(dir_path)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            created.append(str(p))
        else:
            # Ensure it is a directory, not a file
            if not p.is_dir():
                raise ValueError(f"Path exists but is not a directory: {dir_path}")
    
    return created

if __name__ == "__main__":
    created_dirs = create_directories()
    print(f"Created directories: {created_dirs}")
    print("Directory structure setup complete.")