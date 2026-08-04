import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the necessary directory structure for the project.
    Ensures all required directories exist before any processing begins.
    """
    base_dir = Path(__file__).parent.parent
    project_name = "PROJ-756-assessing-dataset-imbalance-effects-on-m"
    
    # Define the project root
    project_root = base_dir / project_name
    
    # Define all required directories
    directories = [
        project_root,
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "contract",
        project_root / "tests" / "integration",
        project_root / "artifacts",
        project_root / "results",
        project_root / "results" / "shap_analysis",
        project_root / "state",
        project_root / "logs",
        project_root / "contracts"
    ]
    
    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create a .gitkeep file in empty directories to ensure they are tracked
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in: {directory}")

def main():
    """
    Main entry point for the setup script.
    """
    create_directories()
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
