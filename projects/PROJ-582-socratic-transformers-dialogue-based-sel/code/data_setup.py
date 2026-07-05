"""
Setup script for data directory structure.
Creates required directories and .gitkeep files for version control.
"""
import os
import sys

# Project root is the parent of 'code'
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# Define required subdirectories
REQUIRED_DIRS = [
    'raw',
    'processed',
    'results'
]

def main():
    """Create data directory structure and .gitkeep files."""
    print(f"Setting up data directory structure at: {DATA_DIR}")

    # Ensure base data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created base directory: {DATA_DIR}")

    # Create subdirectories and .gitkeep files
    for dir_name in REQUIRED_DIRS:
        dir_path = os.path.join(DATA_DIR, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
        
        # Create .gitkeep to ensure directory is tracked by git
        gitkeep_path = os.path.join(dir_path, '.gitkeep')
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, 'w') as f:
                f.write("# Keep this directory in version control\n")
            print(f"Created .gitkeep in: {dir_path}")
        else:
            print(f".gitkeep already exists in: {dir_path}")

    print("Data directory setup complete.")
    return 0

if __name__ == '__main__':
    sys.exit(main())