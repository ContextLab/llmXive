"""
Script to initialize the project directory structure for code modules.
Creates the required subdirectories under the `code/` root.
"""
import os
from pathlib import Path
from typing import List
from config import ensure_directories


def create_directories() -> List[Path]:
    """
    Create the standard code module directories.
    
    Returns:
        List of created directory paths.
    """
    root = Path(__file__).parent.parent
    code_root = root / "code"
    
    directories = [
        code_root,
        code_root / "data",
        code_root / "model",
        code_root / "analysis",
        code_root / "utils",
    ]
    
    created = []
    for dir_path in directories:
        ensure_directories([dir_path])
        created.append(dir_path)
        
    return created


def main():
    """Entry point for directory creation."""
    print("Initializing code module directories...")
    created = create_directories()
    for d in created:
        print(f"  Created: {d}")
    print("Code module structure ready.")


if __name__ == "__main__":
    main()