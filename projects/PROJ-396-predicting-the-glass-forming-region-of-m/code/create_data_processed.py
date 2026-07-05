import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """
    Create the data/processed/ directory as required by task T003.
    """
    # Define the target directory relative to the project root
    # Assuming the script runs from the project root or code/ directory
    # We use a relative path that works from the project root
    project_root = Path(__file__).resolve().parent.parent
    target_dir = project_root / "data" / "processed"

    print(f"Creating directory: {target_dir}")
    success = create_directory(str(target_dir))
    
    if success:
        print(f"Successfully created or verified existence of: {target_dir}")
    else:
        print(f"Failed to create directory: {target_dir}")
        raise RuntimeError(f"Could not create {target_dir}")

if __name__ == "__main__":
    main()