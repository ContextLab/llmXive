"""
Setup data directory structure for the llmXive project.

Creates the following directories:
- data/raw/      : For immutable puzzles and source datasets
- data/processed/: For logs, results, and intermediate analysis
"""
import os
import sys
from pathlib import Path
from typing import List

def setup_data_directories(base_path: Path) -> List[Path]:
    """
    Create the required data directory structure.
    
    Args:
        base_path: The root directory where data folders should be created.
        
    Returns:
        List of created Path objects.
        
    Raises:
        OSError: If directory creation fails.
    """
    data_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
    ]
    
    created_paths = []
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(dir_path)
        # Verify creation
        if not dir_path.exists() or not dir_path.is_dir():
            raise OSError(f"Failed to create directory: {dir_path}")
            
    return created_paths

def main():
    """Entry point for script execution."""
    # Determine project root (assuming script is in code/ directory)
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent
    
    print(f"Setting up data directories in: {project_root}")
    
    try:
        created = setup_data_directories(project_root)
        print("Successfully created directories:")
        for p in created:
            print(f"  - {p}")
        return 0
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())