import os
import sys
from pathlib import Path

def setup_directories():
    """
    Create the required data directory structure atomically using mkdir -p logic.
    
    Creates the following directories relative to the project root:
    - data/raw/
    - data/processed/
    - data/results/
    - state/
    
    Ensures parent directories are created if they don't exist.
    """
    # Determine project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    # Define required directories relative to project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "state"
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        else:
            # Verify it's actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    return {
        "project_root": str(project_root),
        "directories_created": [str(project_root / d) for d in required_dirs],
        "new_directories_count": created_count
    }
