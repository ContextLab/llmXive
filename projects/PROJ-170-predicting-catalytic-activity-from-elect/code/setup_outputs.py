import os
import sys
from pathlib import Path
from config import get_project_root

def create_outputs_directory():
    """
    Creates the 'outputs' directory at the project root if it does not exist.
    This satisfies task T001d.
    """
    project_root = get_project_root()
    outputs_dir = project_root / "outputs"
    
    if not outputs_dir.exists():
        outputs_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {outputs_dir}")
    else:
        print(f"Directory already exists: {outputs_dir}")
    
    return outputs_dir

def main():
    create_outputs_directory()
    return 0

if __name__ == "__main__":
    sys.exit(main())