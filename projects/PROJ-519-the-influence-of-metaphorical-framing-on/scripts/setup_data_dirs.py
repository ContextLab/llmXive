"""
Script to initialize the data directory structure for the project.
Creates `data/raw`, `data/processed`, and `data/derived` directories
with `.gitkeep` files to ensure they are tracked by version control.
"""
import os
import sys

def ensure_dir(path: str) -> None:
    """Create a directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def ensure_gitkeep(path: str) -> None:
    """Create a .gitkeep file if it does not exist."""
    file_path = os.path.join(path, ".gitkeep")
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            f.write("# This file ensures the directory is tracked by git.\n")
        print(f"Created .gitkeep in: {path}")
    else:
        print(f".gitkeep already exists in: {path}")

def main() -> int:
    """Main entry point to setup data directories."""
    base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    # Ensure base data directory exists
    ensure_dir(base_dir)
    
    # Define required subdirectories
    subdirs = [
        os.path.join(base_dir, "raw"),
        os.path.join(base_dir, "processed"),
        os.path.join(base_dir, "derived"),
    ]
    
    for subdir in subdirs:
        ensure_dir(subdir)
        ensure_gitkeep(subdir)
    
    print("Data directory structure initialized successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())