import os
from pathlib import Path

def setup_data_directories(root_dir: str = ".") -> None:
    """
    Create the required data directory structure for the llmXive project.
    
    Creates the following directories relative to root_dir:
    - data/raw/
    - data/processed/
    - data/models/
    
    Args:
        root_dir: The root directory of the project (default: current directory)
    """
    base_path = Path(root_dir)
    data_path = base_path / "data"
    
    directories = [
        "raw",
        "processed",
        "models"
    ]
    
    for dir_name in directories:
        dir_path = data_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        # Ensure the directory is not empty by adding a .gitkeep file
        # This ensures the directory is tracked by git even if empty
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text("# Keep this directory")
        
        print(f"Created: {dir_path}")

if __name__ == "__main__":
    setup_data_directories()
