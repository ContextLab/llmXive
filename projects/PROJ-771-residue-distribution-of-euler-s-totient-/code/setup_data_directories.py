import os
from pathlib import Path

def setup_data_directories():
    """
    Create the required data directory structure for the project.
    
    This function creates:
    - data/raw/ : For raw residue count data (JSON files)
    - data/processed/ : For processed statistical results (JSON files)
    
    Returns:
        bool: True if directories were created successfully, False otherwise.
    """
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    try:
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a .gitkeep file to ensure directories are tracked by git
        (raw_dir / ".gitkeep").touch()
        (processed_dir / ".gitkeep").touch()
        
        return True
    except OSError as e:
        print(f"Error creating data directories: {e}")
        return False

if __name__ == "__main__":
    success = setup_data_directories()
    if success:
        print("Data directories created successfully.")
    else:
        print("Failed to create data directories.")
        exit(1)
