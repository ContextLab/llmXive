import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the required data directory structure for the project.
    
    Directories created:
    - data/raw: For raw, unprocessed data downloads
    - data/processed: For cleaned and transformed datasets
    - data/splits: For train/test split indices (if static splits were used)
    - results: For model outputs, plots, and reports
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the project root based on the script location or CWD
    # The script is expected to be run from the project root or code/ directory
    current_file = Path(__file__).resolve()
    # Assuming script is in code/ or code/code/, we look for 'data' relative to project root
    # If run as 'python code/setup_data_dirs.py', current_file.parent is 'code'
    # We assume project root is parent of 'code'
    project_root = current_file.parent.parent if current_file.name == 'setup_data_dirs.py' else current_file.parent.parent.parent
    
    # Ensure we are in a reasonable directory structure
    # If 'data' exists as a sibling to 'code', use that
    if (current_file.parent.parent / "data").exists():
        data_root = current_file.parent.parent / "data"
    elif (current_file.parent / "data").exists():
        data_root = current_file.parent / "data"
    else:
        # Fallback: create 'data' in current working directory if no structure found
        data_root = Path.cwd() / "data"

    directories = [
        "data/raw",
        "data/processed",
        "data/splits",
        "results"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = Path(dir_path)
        # If dir_path is relative, resolve it against data_root if it looks like a data dir
        # But tasks.md says paths are relative to project root.
        # Let's construct absolute paths relative to the detected project root or CWD
        
        # Normalize path construction:
        if dir_path.startswith("data/"):
            full_path = data_root / Path(dir_path).relative_to("data/")
        elif dir_path == "results":
            full_path = Path.cwd() / dir_path
        else:
            full_path = Path.cwd() / dir_path

        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
            else:
                print(f"Directory already exists: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")
            return False

    if created_count > 0 or all(Path(d).exists() for d in directories):
        print("Data directory structure setup complete.")
        return True
    else:
        print("No directories were created and some might be missing.")
        return False

if __name__ == "__main__":
    success = setup_directories()
    sys.exit(0 if success else 1)
