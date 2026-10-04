import os
import sys
from pathlib import Path

def create_directory(path: str) -> bool:
    """Create a directory if it does not exist.
    
    Args:
        path: The path to the directory to create.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    try:
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """Create the contracts directory under specs/001-llmxive-followup."""
    contracts_dir = "specs/001-llmxive-followup/contracts"
    if create_directory(contracts_dir):
        print(f"Created directory: {contracts_dir}")
        return 0
    else:
        print(f"Failed to create directory: {contracts_dir}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())