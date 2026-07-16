import os
import sys
from pathlib import Path

def main():
    """
    Create the required project directory structure for PROJ-096.
    Executes the equivalent of:
    mkdir -p code/utils code/data data/processed data/checksums tests state/projects
    """
    # Define the project root relative to the current working directory
    # Assuming the script is run from the project root: projects/PROJ-096-exploring-the-role-of-network-topology-o/
    project_root = Path(".")
    
    # Define the directories to create
    directories = [
        "code/utils",
        "code/data",
        "data/processed",
        "data/checksums",
        "tests",
        "state/projects"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    
    # Verify existence
    all_exist = all((project_root / d).exists() for d in directories)
    if not all_exist:
        print("ERROR: Some directories failed to create.")
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())