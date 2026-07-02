import os
from pathlib import Path
from typing import List

def create_data_directories(base_path: Path) -> List[str]:
    """
    Creates the required data directory structure for the project.
    
    Specifically creates:
    - data/raw/
    - data/processed/
    
    Each directory is initialized with a .gitkeep file to ensure 
    they are tracked by git even when empty.
    
    Args:
        base_path: The root path of the project where 'data' directory should be created.
        
    Returns:
        List of created directory paths as strings.
    """
    data_dir = base_path / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    directories = [raw_dir, processed_dir]
    created_paths = []
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
        
        created_paths.append(str(directory))
        print(f"Created directory: {directory}")
        
    return created_paths

def main():
    """
    Main entry point for setting up data directories.
    Assumes the script is run from the project root.
    """
    base_path = Path(__file__).parent.parent
    created = create_data_directories(base_path)
    print(f"Successfully created {len(created)} data directories.")

if __name__ == "__main__":
    main()