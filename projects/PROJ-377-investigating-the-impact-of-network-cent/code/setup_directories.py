"""
Script to initialize the project directory structure for llmXive research pipeline.
Creates the required directory hierarchy under 'code/' as specified in T005a.
"""
import os
from pathlib import Path

def setup_directories():
    """
    Creates the core project directories:
    - code/
    - code/data/
    - code/analysis/
    - code/utils/
    
    This function is idempotent and will not fail if directories already exist.
    """
    base_dir = Path(__file__).resolve().parent.parent
    code_dir = base_dir / "code"
    
    directories = [
        code_dir,
        code_dir / "data",
        code_dir / "analysis",
        code_dir / "utils",
    ]
    
    created = []
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path.relative_to(base_dir)))
            print(f"Created directory: {dir_path.relative_to(base_dir)}")
        else:
            print(f"Directory already exists: {dir_path.relative_to(base_dir)}")
    
    if not created:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {len(created)} directories.")
    
    return created

if __name__ == "__main__":
    setup_directories()
