import os
import sys
from pathlib import Path

def main():
    """
    Creates the required code directory structure for the project.
    Specifically creates: code/data/, code/tests/, code/utils/
    """
    # Determine the project root based on the script location or current working directory
    # The task specifies paths relative to the project root.
    # We assume the script is run from the project root or the project root is the parent of 'code'.
    project_root = Path.cwd()
    
    code_dir = project_root / "code"
    
    directories_to_create = [
        code_dir / "data",
        code_dir / "tests",
        code_dir / "utils"
    ]
    
    created_count = 0
    for directory in directories_to_create:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    if created_count > 0:
        print(f"Successfully created {created_count} directory(ies).")
    else:
        print("All required directories already exist.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
