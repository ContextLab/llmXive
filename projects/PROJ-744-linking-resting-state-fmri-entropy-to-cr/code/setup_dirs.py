import os
import sys
from pathlib import Path

def create_directory(path: str) -> bool:
    """
    Create a directory at the specified path if it does not exist.
    
    Args:
        path: Relative or absolute path to the directory to create.
        
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
    """
    Main entry point to create required project directories.
    This function specifically handles T001d: creating data/logs.
    """
    # Define the directory for T001d
    log_dir = "data/logs"
    
    print(f"Creating directory: {log_dir}")
    if create_directory(log_dir):
        print(f"Successfully created or verified existence of: {log_dir}")
        
        # Verify creation by listing contents (should be empty initially)
        if os.path.exists(log_dir):
            print(f"Contents of {log_dir}: {os.listdir(log_dir)}")
        else:
            print(f"Warning: Directory {log_dir} was not found after creation attempt.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Failed to create directory: {log_dir}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()