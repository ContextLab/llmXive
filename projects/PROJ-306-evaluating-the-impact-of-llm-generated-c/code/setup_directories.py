import os
import sys

def create_directory(path: str) -> bool:
    """
    Creates a directory at the specified path if it does not already exist.
    
    Args:
        path (str): The relative or absolute path to the directory.
        
    Returns:
        bool: True if the directory was created or already exists, False on error.
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            return True
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point to create the required project directory structure.
    Creates benchmarks, raw, processed, generated, coverage_reports, and outputs directories.
    """
    base_dir = "data"
    
    # Define the directory structure to create
    directories = [
        os.path.join(base_dir, "benchmarks"),
        os.path.join(base_dir, "benchmarks", "raw"),
        os.path.join(base_dir, "benchmarks", "processed"),
        os.path.join(base_dir, "generated"),
        os.path.join(base_dir, "coverage_reports"),
        os.path.join(base_dir, "processed"),
        "outputs"
    ]
    
    print("Creating project directory structure...")
    success = True
    for directory in directories:
        if create_directory(directory):
            print(f"Created/Verified: {directory}")
        else:
            success = False
    
    if success:
        print("Directory structure setup complete.")
        return 0
    else:
        print("Some directories failed to create.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
