import os
import sys
from pathlib import Path

def main():
    """
    Create the required code directory structure for the fracture toughness prediction project.
    
    Directories to create:
    - code/
    - code/data/
    - code/models/
    - code/train/
    - code/explain/
    """
    project_root = Path(__file__).resolve().parent.parent
    base_code_dir = project_root / "code"
    
    # Define directories to create
    directories = [
        base_code_dir,
        base_code_dir / "data",
        base_code_dir / "models",
        base_code_dir / "train",
        base_code_dir / "explain",
    ]
    
    created = []
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path.relative_to(project_root)))
            print(f"Created directory: {dir_path.relative_to(project_root)}")
        else:
            print(f"Directory already exists: {dir_path.relative_to(project_root)}")
    
    if not created:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {len(created)} directory/directories.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())