"""
Setup script to initialize the data directory structure for the project.
Creates the following directories under the project root:
- data/raw/
- data/processed/
- data/contracts/
- data/figures/
- data/audit_logs/
"""
import os
from pathlib import Path

def setup_data_directories():
    """Create the required data directory structure."""
    # Define the base data directory relative to the script location
    # Assuming this script is run from the project root or code/ directory
    # We look for the 'data' directory relative to the current working directory
    # or the script's parent directory if run as a module.
    
    # Determine project root: assume current working directory is project root
    # or check if we are in code/
    current_dir = Path.cwd()
    
    # Check if we are inside a 'code' directory
    if current_dir.name == 'code':
        project_root = current_dir.parent
    else:
        project_root = current_dir

    data_dir = project_root / 'data'
    raw_dir = data_dir / 'raw'
    processed_dir = data_dir / 'processed'
    contracts_dir = data_dir / 'contracts'
    figures_dir = data_dir / 'figures'
    audit_logs_dir = data_dir / 'audit_logs'

    directories = [
        raw_dir,
        processed_dir,
        contracts_dir,
        figures_dir,
        audit_logs_dir
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    # Initialize .gitkeep files to ensure directories are tracked by git
    gitkeep_content = "# This file ensures the directory is tracked by git.\n"
    for directory in directories:
        gitkeep_path = directory / '.gitkeep'
        with open(gitkeep_path, 'w') as f:
            f.write(gitkeep_content)
        print(f"Created .gitkeep in: {directory}")

    # Initialize an empty audit log file structure if needed
    # Though T008 handles the actual logging logic, we ensure the path exists.
    # The task specifically asks for contracts/ which is a directory for schema definitions.
    
    print(f"\nData directory structure successfully created at: {data_dir}")
    return True

if __name__ == '__main__':
    setup_data_directories()