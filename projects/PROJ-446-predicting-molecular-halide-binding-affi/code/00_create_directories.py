import os
from pathlib import Path

def main():
    """
    Create the essential project directory structure for PROJ-446.
    Specifically creates code/ and code/utils/ directories.
    """
    # Determine project root based on the file location
    # Assuming this script is run from the project root or the script is in the root
    # We construct paths relative to the current working directory to ensure
    # they land in the correct project folder.
    project_root = Path.cwd()
    
    # Define the directories to create as per T002
    # Path relative to project root: code/ and code/utils/
    code_dir = project_root / "code"
    utils_dir = code_dir / "utils"
    
    dirs_to_create = [code_dir, utils_dir]
    
    created = []
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    if not created:
        print("All required directories for T002 already exist.")
    
    return created

if __name__ == "__main__":
    main()