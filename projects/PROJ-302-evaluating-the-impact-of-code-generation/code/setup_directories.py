"""
Directory creation utilities for the llmXive project.
This module handles the creation of the required project structure.
"""
import os
from pathlib import Path

def create_directories():
    """
    Creates the necessary directory structure for the project.
    
    Creates:
    - code/data_acquisition/
    - code/feature_extraction/
    - code/analysis/
    - code/utils/
    
    Returns:
        list: A list of created directory paths as strings.
    """
    project_root = Path(__file__).resolve().parent.parent
    base_code_dir = project_root / "code"
    
    required_dirs = [
        "data_acquisition",
        "feature_extraction",
        "analysis",
        "utils"
    ]
    
    created_dirs = []
    
    for dir_name in required_dirs:
        dir_path = base_code_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create __init__.py files in each new directory to make them Python packages
    for dir_name in required_dirs:
        dir_path = base_code_dir / dir_name
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created package init: {init_file}")
    
    return created_dirs

if __name__ == "__main__":
    create_directories()
    print("Directory setup complete.")