import os
from pathlib import Path

def setup_directories():
    """
    Creates the required directory structure for the PROJ-066 project.
    Ensures existence of data/raw, data/processed, code/data, code/models,
    code/utils, and tests directories relative to the project root.
    """
    # Determine project root (assuming script runs from project root or code/)
    # We use the directory of this script as the anchor if run from code/, 
    # otherwise we assume current working directory is root.
    script_path = Path(__file__).resolve()
    # If the script is in code/, go up one level to root
    if script_path.parent.name == "code":
        root = script_path.parent.parent
    else:
        # Fallback to cwd if structure is different
        root = Path.cwd()

    directories = [
        "data/raw",
        "data/processed",
        "code/data",
        "code/models",
        "code/utils",
        "tests",
        "figures" # Added for visualization outputs mentioned in tasks
    ]

    created = []
    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
        else:
            # Ensure it is a directory, not a file
            if not dir_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {dir_path}")

    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All required directories already exist.")
    
    return created

if __name__ == "__main__":
    setup_directories()