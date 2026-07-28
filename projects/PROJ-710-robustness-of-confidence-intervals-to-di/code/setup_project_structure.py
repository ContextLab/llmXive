"""
Project Setup Script for PROJ-710
Creates the required directory structure for the research project.
"""
import os
from pathlib import Path

def main():
    """
    Creates the project directory structure as specified in T001a.
    Paths are relative to the project root.
    """
    # Define the base project path
    base_path = Path("projects/PROJ-710-robustness-of-confidence-intervals-to-di")
    
    # Define the required directories
    directories = [
        base_path / "code",
        base_path / "code" / "data",
        base_path / "code" / "analysis",
        base_path / "code" / "utils",
        base_path / "code" / "tests",
        base_path / "artifacts",
    ]
    
    # Create directories if they don't exist
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created: {directory}")
            created_count += 1
        else:
            print(f"Exists: {directory}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
