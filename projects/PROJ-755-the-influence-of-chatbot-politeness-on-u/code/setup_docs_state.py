"""
Task T001d: Create documentation directories: `docs`, `state`.

This script ensures the existence of the `docs` and `state` directories
at the project root, along with placeholder files to ensure they are
tracked by version control and satisfy the requirement for non-empty directories.
"""
import os
import sys
from pathlib import Path
from typing import List

# Define the project root relative to this script's location
# Assuming this script is in code/, project root is one level up
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories to create
TARGET_DIRS = [
    "docs",
    "state"
]

# Placeholder files to create inside each directory if empty
# This ensures the directories are not empty and can be committed
PLACEHOLDER_CONTENTS = {
    "docs": {
        "README.md": "# Documentation\n\nThis directory contains project documentation.",
        "quickstart.md": "# Quick Start Guide\n\nInstructions for running the pipeline."
    },
    "state": {
        "README.md": "# State Directory\n\nThis directory contains project state and metadata.",
        ".gitkeep": ""
    }
}

def ensure_directories() -> List[str]:
    """
    Creates the required directories and placeholder files.
    
    Returns:
        List[str]: A list of created/verified paths.
    """
    created_paths = []
    
    for dir_name in TARGET_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        
        # Create directory if it doesn't exist
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
        
        # Ensure placeholder files exist
        if dir_name in PLACEHOLDER_CONTENTS:
            for filename, content in PLACEHOLDER_CONTENTS[dir_name].items():
                file_path = dir_path / filename
                if not file_path.exists():
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"Created placeholder file: {file_path}")
                else:
                    print(f"Placeholder file already exists: {file_path}")
        
        created_paths.append(str(dir_path))
    
    return created_paths

def main():
    """Entry point for the script."""
    print(f"Project Root: {PROJECT_ROOT}")
    print("Creating documentation and state directories...")
    
    try:
        paths = ensure_directories()
        print("\nSuccess! Created/Verified directories:")
        for p in paths:
            print(f"  - {p}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()