"""
Setup script for the llmXive data directory structure.
Creates the required directories for raw, derived, gold standard data, and artifacts.
"""
import os
from pathlib import Path
import sys

# Ensure the code directory is in the path for imports if running as script
# Although this script is standalone, we ensure it runs from the project root context
def setup_directories():
    """
    Creates the standard data directory structure required by the project.
    Directories created:
    - data/raw/
    - data/derived/
    - data/gold_standard/
    - artifacts/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    base_dir = Path.cwd()
    
    # Define the required directories relative to the project root
    directories = [
        base_dir / "data" / "raw",
        base_dir / "data" / "derived",
        base_dir / "data" / "gold_standard",
        base_dir / "artifacts"
    ]
    
    created_count = 0
    for dir_path in directories:
        try:
            # Create parent directories if they don't exist
            dir_path.mkdir(parents=True, exist_ok=True)
            # Create a .gitkeep file to ensure the directory is tracked by git
            # This prevents empty directories from being ignored
            gitkeep_path = dir_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.touch()
            created_count += 1
            print(f"Created/Verified directory: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
            return False
    
    print(f"Successfully setup {created_count} data directories.")
    return True

if __name__ == "__main__":
    success = setup_directories()
    sys.exit(0 if success else 1)
