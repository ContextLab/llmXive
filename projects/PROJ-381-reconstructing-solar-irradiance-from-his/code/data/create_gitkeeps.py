"""
Utility script to create .gitkeep files in data directories.

This ensures that empty directories are tracked by git.
"""

import os
from pathlib import Path

def main():
    """Create .gitkeep files in data directories."""
    project_root = Path(__file__).parent.parent.parent
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
    ]
    
    for data_dir in data_dirs:
        data_dir.mkdir(parents=True, exist_ok=True)
        gitkeep_file = data_dir / ".gitkeep"
        if not gitkeep_file.exists():
            gitkeep_file.touch()
            print(f"Created: {gitkeep_file}")
        else:
            print(f"Already exists: {gitkeep_file}")

if __name__ == "__main__":
    main()