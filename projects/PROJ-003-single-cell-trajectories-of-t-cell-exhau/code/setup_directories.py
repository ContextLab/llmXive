import os
from pathlib import Path

def setup_directories(project_root: Path) -> None:
    """
    Create the required directory structure for the project.
    
    Creates:
      - data/raw/
      - data/processed/
      - data/results/
      - tests/unit/
      - tests/integration/
      
    Args:
        project_root: The root path of the project (e.g., projects/PROJ-003-...)
    """
    # Define the directory structure relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/integration",
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

if __name__ == "__main__":
    # Default to current directory if no argument provided, 
    # but typically this is called from a script with a specific root
    root = Path.cwd()
    setup_directories(root)
    print("Directory structure setup complete.")