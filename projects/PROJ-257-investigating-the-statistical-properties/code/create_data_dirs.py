import os
from pathlib import Path


def create_directories():
    """
    Creates the required directory structure for the project.
    
    Creates:
    - data/raw/
    - data/processed/
    - output/results/
    - output/figures/
    
    Also creates .gitkeep files in each directory to ensure they are tracked by git.
    """
    # Define the base directories relative to the project root
    base_dirs = {
        "data/raw",
        "data/processed",
        "output/results",
        "output/figures",
    }

    for dir_path in base_dirs:
        full_path = Path(dir_path)
        full_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = full_path / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created directory: {full_path}")
        print(f"Created .gitkeep: {gitkeep_path}")


def main():
    """Entry point for the script."""
    print("Creating data and output directory structure...")
    create_directories()
    print("Directory structure created successfully.")


if __name__ == "__main__":
    main()