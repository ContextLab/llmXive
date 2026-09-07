"""
Script to initialize the project directory structure for llmXive follow-up.
Creates the required data directory and subdirectories with .gitkeep files.
"""
import os
from pathlib import Path

def setup_data_directories():
    """
    Creates the data directory structure required for the project.
    
    Structure created:
    - projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/
    - projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/raw/
    - projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/processed/
    - projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/data/artifacts/
    
    Each subdirectory contains a .gitkeep file to ensure directory persistence in git.
    """
    base_path = Path("projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff")
    data_path = base_path / "data"
    
    # Create main data directory
    data_path.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {data_path}")
    
    # Define subdirectories
    subdirs = [
        "raw",
        "processed", 
        "artifacts"
    ]
    
    for subdir_name in subdirs:
        subdir_path = data_path / subdir_name
        subdir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {subdir_path}")
        
        # Create .gitkeep file
        gitkeep_path = subdir_path / ".gitkeep"
        gitkeep_path.write_text("# Git keep file to preserve directory structure\n")
        print(f"Created .gitkeep in: {gitkeep_path}")
    
    # Create the main data/.gitkeep as well
    main_gitkeep = data_path / ".gitkeep"
    main_gitkeep.write_text("# Git keep file to preserve directory structure\n")
    print(f"Created .gitkeep in: {main_gitkeep}")
    
    print("\nData directory structure setup complete.")
    return True

def main():
    """Entry point for the directory setup script."""
    try:
        setup_data_directories()
        print("\nSuccess: All data directories created successfully.")
        return 0
    except Exception as e:
        print(f"\nError during directory setup: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
