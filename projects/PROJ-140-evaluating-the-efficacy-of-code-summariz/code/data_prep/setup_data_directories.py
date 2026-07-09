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
    
    Ensures all directories exist, creating them if necessary.
    """
    # Define the base data directory relative to the project root
    # Assuming the script is run from the project root or code/data_prep
    project_root = Path(__file__).resolve().parent.parent.parent
    data_root = project_root / "data"
    
    required_dirs = [
        "defects4j",
        "summaries",
        "interaction_logs",
        "analysis_results",
        "consent"
    ]
    
    created_dirs = []
    for dir_name in required_dirs:
        dir_path = data_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
        else:
            # Ensure it's actually a directory
            if not dir_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {dir_path}")
    
    return created_dirs

def main():
    """Entry point for CLI execution."""
    print("Setting up data directory structure...")
    try:
        created = setup_data_directories()
        print("Successfully created/verified directories:")
        for d in created:
            print(f"  - {d}")
        if not created:
            print("All directories already exist.")
        return 0
    except Exception as e:
        print(f"Error setting up data directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
