import os
import sys
from pathlib import Path
from typing import Optional

def ensure_processed_directory(base_path: Optional[str] = None) -> bool:
    """
    Creates and verifies the 'data/processed' directory.
    
    Args:
        base_path: Optional base project root. If None, uses current working directory.
        
    Returns:
        True if the directory exists and is writable after the operation.
        
    Raises:
        RuntimeError: If directory creation fails or verification fails.
    """
    if base_path is None:
        base_path = os.getcwd()
        
    project_root = Path(base_path)
    processed_dir = project_root / "data" / "processed"
    
    try:
        processed_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Failed to create directory {processed_dir}: {e}")
    
    if not processed_dir.exists():
        raise RuntimeError(f"Directory {processed_dir} does not exist after creation attempt.")
        
    if not processed_dir.is_dir():
        raise RuntimeError(f"Path {processed_dir} exists but is not a directory.")
        
    # Verify writability by attempting to create a temporary marker file
    marker_file = processed_dir / ".write_test"
    try:
        marker_file.touch(exist_ok=False)
        marker_file.unlink()
    except OSError as e:
        raise RuntimeError(f"Directory {processed_dir} is not writable: {e}")
        
    return True

def main():
    """Main entry point for script execution."""
    print("Ensuring 'data/processed' directory exists...")
    try:
        success = ensure_processed_directory()
        if success:
            print("Successfully verified 'data/processed' directory.")
            return 0
        else:
            print("Failed to ensure directory.", file=sys.stderr)
            return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())