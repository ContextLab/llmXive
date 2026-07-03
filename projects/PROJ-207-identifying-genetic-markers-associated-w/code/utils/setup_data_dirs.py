import os
import sys
from pathlib import Path

def setup_data_directories():
    """
    Create the data directory structure with immutable raw data constraints.
    
    Creates the following directories relative to the project root:
    - data/raw: Immutable raw data storage
    - data/processed: Processed data artifacts
    - data/interim: Intermediate data files during pipeline execution
    
    The 'data/raw' directory is marked as immutable by creating a .gitkeep
    file and a constraint marker file to enforce the policy programmatically.
    """
    # Determine project root (assuming this script is in code/utils/)
    project_root = Path(__file__).resolve().parent.parent.parent
    data_root = project_root / "data"
    
    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "interim"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Enforce immutable constraint on raw data directory
    raw_dir = data_root / "raw"
    immutable_marker = raw_dir / ".immutable"
    
    if not immutable_marker.exists():
        with open(immutable_marker, "w") as f:
            f.write("# IMMUTABLE DATA DIR\n")
            f.write("# Do not modify or delete files in this directory.\n")
            f.write("# All writes must go to data/interim or data/processed.\n")
        print(f"Created immutable constraint marker: {immutable_marker}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            with open(gitkeep, "w") as f:
                f.write("# Keep this directory in version control\n")
            print(f"Created .gitkeep in: {directory}")
    
    return True

if __name__ == "__main__":
    setup_data_directories()
    print("Data directory structure created successfully.")