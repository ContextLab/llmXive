"""
Script to setup the data directory structure for the llmXive project.
Creates required directories and .gitkeep files to ensure they are tracked by git.
"""
import os
from pathlib import Path

def setup_data_directories():
    """
    Creates the following directory structure under the project root:
    - data/raw/
    - data/processed/
    - data/processed/plots/

    Ensures each directory contains a .gitkeep file.
    """
    # Define the base data directory relative to the project root
    # Assuming this script runs from code/ or project root, we use a relative path
    # The task specifies paths relative to project root.
    # We assume the script is run from the project root or code/ directory.
    # To be safe, we resolve relative to the script's location if needed,
    # but standard practice for this pipeline is to run from root.
    # Let's assume the script is in code/ and data/ is at root.
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent if script_dir.name == 'code' else script_dir
    
    base_data_dir = project_root / "data"
    raw_dir = base_data_dir / "raw"
    processed_dir = base_data_dir / "processed"
    plots_dir = processed_dir / "plots"

    directories = [raw_dir, processed_dir, plots_dir]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created: {gitkeep_path}")
        else:
            print(f"Exists: {gitkeep_path}")

    print(f"Data directory structure setup complete at {base_data_dir}")

if __name__ == "__main__":
    setup_data_directories()