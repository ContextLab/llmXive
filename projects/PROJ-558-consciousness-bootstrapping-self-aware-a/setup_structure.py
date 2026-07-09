"""
Script to initialize the directory structure for the Consciousness Bootstrapping project.
Creates the required subdirectories under the project root.
"""
import os
from pathlib import Path

def create_directories():
    """Create the project directory structure."""
    base_path = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    # Define the required subdirectories relative to the base path
    subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts",
        "artifacts/results"
    ]
    
    created_count = 0
    for subdir in subdirs:
        full_path = base_path / subdir
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nSetup complete. {created_count} new directories created.")
    return created_count

if __name__ == "__main__":
    create_directories()