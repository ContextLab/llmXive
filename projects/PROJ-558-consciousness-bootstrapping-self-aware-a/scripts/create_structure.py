"""
Script to create the directory structure for the Consciousness Bootstrapping project.
This script must be run to initialize the project folders as per task T001a.
"""
import os
from pathlib import Path

def main():
    project_root = Path("projects/PROJ-558-consciousness-bootstrapping-self-aware-a")
    
    # Define the required subdirectories
    subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts",
        "artifacts/results"
    ]
    
    # Create directories
    for subdir in subdirs:
        dir_path = project_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    print(f"Directory structure for {project_root} created successfully.")

if __name__ == "__main__":
    main()