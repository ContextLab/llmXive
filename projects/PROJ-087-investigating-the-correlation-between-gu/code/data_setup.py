import os
from pathlib import Path

def setup_data_directories():
    """
    Setup the data directory structure for the project.
    Creates:
      - data/raw/
      - data/processed/
      - data/processed/plots/
    
    Ensures each directory contains a .gitkeep file to preserve them in version control.
    """
    base_dir = Path("data")
    raw_dir = base_dir / "raw"
    processed_dir = base_dir / "processed"
    plots_dir = processed_dir / "plots"

    directories = [raw_dir, processed_dir, plots_dir]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in {directory}")
        else:
            print(f"Directory {directory} already exists with .gitkeep")

    print("Data directory structure setup complete.")

if __name__ == "__main__":
    setup_data_directories()