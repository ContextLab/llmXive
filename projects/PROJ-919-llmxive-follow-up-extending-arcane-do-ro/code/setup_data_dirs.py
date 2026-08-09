import os
from pathlib import Path
import sys

def setup_directories():
    """
    Creates the required data directory structure for the llmXive project.
    Directories created:
      - data/raw/
      - data/derived/
      - data/gold_standard/
      - artifacts/
    
    This ensures the project has the necessary folder hierarchy before
    data processing or experiment execution begins.
    """
    # Determine project root (assuming script is in code/ or code/scripts/)
    # We look for the 'data' directory relative to the script location or root
    script_path = Path(__file__).resolve()
    # If the script is in code/, go up one level to project root
    if script_path.name == 'setup_data_dirs.py' and script_path.parent.name == 'code':
        project_root = script_path.parent.parent
    else:
        # Fallback: assume current directory is project root or parent
        project_root = script_path.parent.parent if script_path.parent.name == 'code' else script_path.parent
    
    # If we are running from 'code/scripts/', project_root might be 'code'
    # Let's ensure we are at the root where 'data' and 'artifacts' belong
    # Standard convention: data/ and artifacts/ are at project root
    
    # Check if we are in a nested structure like code/scripts/
    if script_path.parent.name == 'scripts':
        project_root = script_path.parent.parent.parent
    elif script_path.parent.name == 'code':
        project_root = script_path.parent.parent
    
    data_root = project_root / "data"
    artifacts_root = project_root / "artifacts"
    
    directories = [
        data_root / "raw",
        data_root / "derived",
        data_root / "gold_standard",
        artifacts_root
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")
    
    return True

if __name__ == "__main__":
    setup_directories()
