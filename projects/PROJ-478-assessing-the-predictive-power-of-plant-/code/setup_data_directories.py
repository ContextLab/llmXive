"""
Script to create the required data directory structure for the project.
This fulfills task T001b: Create `data/raw`, `data/processed`, `data/metadata`, `results` directories.
"""
import os
import sys
from pathlib import Path

def create_data_directories():
    """
    Creates the standard data and results directory structure relative to the project root.
    
    Directories created:
    - data/raw: For raw, unprocessed data downloads (GBIF, WorldClim, TRY)
    - data/processed: For cleaned, thinned, and aligned data
    - data/metadata: For data dictionaries, provenance logs, and checksums
    - results: For model outputs, figures, and statistical reports
    """
    # Determine project root (assuming script is in code/)
    # If run from root, adjust accordingly. Standardizing to relative from execution context.
    base_path = Path(".")
    
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "metadata",
        base_path / "results",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    # and are not empty on some systems.
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created placeholder: {gitkeep}")
    
    print(f"Data directory structure setup complete. Created {created_count} new directories.")
    return True

if __name__ == "__main__":
    success = create_data_directories()
    sys.exit(0 if success else 1)