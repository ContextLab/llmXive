"""
Setup script to create the project directory structure.
Creates all root directories and subdirectories defined in the implementation plan.
"""
import os
from pathlib import Path

def create_project_structure():
    """
    Creates the full project directory tree.
    
    Structure:
    - code/ (with subdirs: utils, ingestion, processing, analysis, tests)
    - data/ (with subdirs: raw, processed, metadata)
    - outputs/ (with subdirs: reports, figures)
    - docs/
    - state/
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define all directories to create
    directories = [
        # Code structure
        "code",
        "code/utils",
        "code/ingestion",
        "code/processing",
        "code/analysis",
        "code/tests",
        
        # Data structure
        "data",
        "data/raw",
        "data/raw/millennium",
        "data/processed",
        "data/processed/matched_chunks",
        "data/metadata",
        
        # Outputs structure
        "outputs",
        "outputs/reports",
        "outputs/figures",
        
        # Documentation
        "docs",
        
        # State tracking
        "state"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return project_root

if __name__ == "__main__":
    root = create_project_structure()
    print(f"Project root: {root}")
