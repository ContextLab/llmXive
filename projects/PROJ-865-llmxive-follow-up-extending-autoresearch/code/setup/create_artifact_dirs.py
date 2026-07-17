import os
import sys
from pathlib import Path

def create_directory_structure(base_path: str) -> bool:
    """
    Creates the data/artifacts directory structure at the repository root.
    
    Args:
        base_path: The repository root path (typically '.')
        
    Returns:
        True if directory was created successfully, False otherwise.
    """
    try:
        artifacts_dir = Path(base_path) / "data" / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify the directory exists
        if artifacts_dir.exists() and artifacts_dir.is_dir():
            print(f"Successfully created directory: {artifacts_dir}")
            return True
        else:
            print(f"Failed to create directory: {artifacts_dir}")
            return False
            
    except Exception as e:
        print(f"Error creating directory structure: {e}")
        return False

def main():
    """
    Main entry point for creating the data/artifacts directory.
    """
    # Get repository root (assuming script is run from root or code/setup/)
    base_path = Path(__file__).parent.parent.parent
    if not base_path.exists():
        base_path = Path.cwd()
        
    success = create_directory_structure(str(base_path))
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()