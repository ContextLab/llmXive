import os
import sys
from pathlib import Path

def setup_data_directories():
    """
    Creates the required data directory structure for the project.
    
    Directories created:
    - data/defects4j
    - data/summaries
    - data/interaction_logs
    - data/analysis_results
    - data/consent
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the project root (assumed to be the parent of the 'code' directory)
    # This script is located at code/data_prep/setup_data_directories.py
    # So project root is 2 levels up
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    
    data_dir = project_root / "data"
    
    required_dirs = [
        "defects4j",
        "summaries",
        "interaction_logs",
        "analysis_results",
        "consent"
    ]
    
    created_dirs = []
    failed_dirs = []
    
    for dir_name in required_dirs:
        dir_path = data_dir / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        except OSError as e:
            failed_dirs.append((dir_name, str(e)))
            print(f"Failed to create directory {dir_name}: {e}", file=sys.stderr)
    
    if failed_dirs:
        print(f"\nWarning: {len(failed_dirs)} directories could not be created.", file=sys.stderr)
        return False
    
    print(f"\nSuccessfully created {len(created_dirs)} data directories.")
    return True

if __name__ == "__main__":
    success = setup_data_directories()
    sys.exit(0 if success else 1)
