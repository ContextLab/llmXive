import os
from pathlib import Path

def setup_directories():
    """
    Create the required data directory structure for the project.
    Creates data/raw/, data/processed/, and data/artifacts/ directories.
    
    Returns:
        bool: True if all directories were created or already exist successfully.
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_root = base_dir / "data"
    
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "artifacts"
    ]
    
    created = False
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created = True
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    return True

if __name__ == "__main__":
    setup_directories()
    print("Directory setup complete.")