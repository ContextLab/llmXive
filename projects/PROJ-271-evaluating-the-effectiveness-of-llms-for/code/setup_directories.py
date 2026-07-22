import os
from pathlib import Path

def create_project_directories():
    """
    Create the required directory structure for the project.
    
    Creates:
    - data/raw/
    - data/processed/
    - results/
    
    This function is idempotent and will not raise errors if directories
    already exist.
    """
    base_path = Path(__file__).resolve().parent.parent
    project_root = base_path / "projects" / "PROJ-271-evaluating-the-effectiveness-of-llms-for"
    
    # Define directory paths
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    results_dir = project_root / "results"
    
    # Create directories
    directories = [
        data_raw,
        data_processed,
        results_dir
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    return True
