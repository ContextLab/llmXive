"""
Module to ensure the existence of the data/raw/ directory.
This script creates the directory if it does not exist and verifies its creation.
"""
import os
import sys
from pathlib import Path

def ensure_raw_directory(base_path: Optional[Path] = None) -> bool:
    """
    Ensures that the data/raw/ directory exists within the project structure.
    
    Args:
        base_path: Optional base path for the project. If None, uses current directory.
        
    Returns:
        bool: True if the directory exists or was successfully created, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    raw_dir = base_path / "data" / "raw"
    
    try:
        raw_dir.mkdir(parents=True, exist_ok=True)
        # Verify the directory actually exists and is a directory
        if raw_dir.exists() and raw_dir.is_dir():
            print(f"Successfully ensured directory exists: {raw_dir}")
            return True
        else:
            print(f"Error: Directory creation verification failed for {raw_dir}")
            return False
    except PermissionError:
        print(f"Error: Permission denied creating directory {raw_dir}")
        return False
    except Exception as e:
        print(f"Error creating directory {raw_dir}: {e}")
        return False

def main():
    """Main entry point for the script."""
    # Use the project root relative to this script's location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    success = ensure_raw_directory(project_root)
    
    if not success:
        sys.exit(1)
    else:
        # List contents to provide verification evidence
        raw_dir = project_root / "data" / "raw"
        print(f"Contents of {raw_dir}:")
        try:
            contents = list(raw_dir.iterdir())
            if not contents:
                print("  (empty)")
            else:
                for item in contents:
                    print(f"  - {item.name}")
        except Exception as e:
            print(f"  Error listing contents: {e}")
        
        sys.exit(0)

if __name__ == "__main__":
    main()
