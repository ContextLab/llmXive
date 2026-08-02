import os
from pathlib import Path

def setup_data_directories(project_root: Path) -> None:
    """
    Create the required data directory structure for the project.
    
    This implements Task T006: Create data/raw/, data/interim/, data/processed/, 
    and data/external/ directory structures.
    
    Args:
        project_root: The root path of the project (e.g., PROJ-273-...)
    """
    # Define the required data directories relative to project root
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "interim",
        project_root / "data" / "processed",
        project_root / "data" / "external",
    ]
    
    # Create each directory (parents=True ensures intermediate dirs are created)
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create a .gitkeep file in each directory to ensure they are tracked by git
    for dir_path in data_dirs:
        gitkeep_path = dir_path / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created .gitkeep in: {dir_path}")
    
    print("Data directory structure setup complete.")

if __name__ == "__main__":
    # When run directly, create directories in the current working directory
    project_root = Path.cwd()
    setup_data_directories(project_root)