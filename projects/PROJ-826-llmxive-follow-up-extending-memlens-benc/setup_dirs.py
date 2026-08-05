"""
Script to create the required project directory structure for PROJ-826.
This script ensures all necessary directories exist before running the pipeline.
"""
import os
from pathlib import Path

def create_project_structure():
    """Create the standard llmXive project directory structure."""
    base_path = Path(__file__).parent
    
    # Define required directories relative to project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "state/projects"
    ]
    
    created = []
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            print(f"Directory already exists: {full_path}")
    
    if created:
        print(f"Created {len(created)} directories:")
        for d in created:
            print(f"  - {d}")
    else:
        print("All required directories already exist.")
    
    return created

if __name__ == "__main__":
    create_project_structure()
