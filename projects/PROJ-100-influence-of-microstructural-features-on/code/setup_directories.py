import os
import sys

def ensure_directories():
    """
    Create the necessary directory structure for the project artifacts.
    Creates 'results/' and 'results/plots/' if they do not exist.
    
    Returns:
        bool: True if directories were created or already existed, False on error.
    """
    directories = [
        "results",
        "results/plots"
    ]
    
    for dir_path in directories:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                print(f"Created directory: {dir_path}")
            else:
                print(f"Directory already exists: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
            return False
    
    return True

if __name__ == "__main__":
    success = ensure_directories()
    sys.exit(0 if success else 1)