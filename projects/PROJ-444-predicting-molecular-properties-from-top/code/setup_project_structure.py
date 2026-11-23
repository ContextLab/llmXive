"""
Project Structure Initialization Script.

This script creates the required directory structure for the
PROJ-444-predicting-molecular-properties-from-top project.
"""
import os
import sys
from pathlib import Path
from typing import List

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists. Create it if it doesn't.
    
    Args:
        path: The directory path to ensure exists.
        
    Returns:
        True if the directory exists (was created or already present), False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def initialize_readme(project_root: Path, content: str) -> bool:
    """
    Initialize a README.md file with the given content.
    
    Args:
        project_root: The root directory of the project.
        content: The text content to write to the README.
        
    Returns:
        True if the file was written successfully, False otherwise.
    """
    readme_path = project_root / "README.md"
    try:
        readme_path.write_text(content, encoding="utf-8")
        return True
    except OSError as e:
        print(f"Error writing README.md: {e}", file=sys.stderr)
        return False

def main() -> int:
    """
    Main entry point for the project structure setup.
    
    Creates the directory structure and README for PROJ-444.
    
    Returns:
        0 on success, 1 on failure.
    """
    project_root = Path("projects/PROJ-444-predicting-molecular-properties-from-top")
    
    # Define required directories
    required_dirs: List[Path] = [
        project_root,
        project_root / "code",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "logs",
        project_root / "tests",
        project_root / "reports",
        project_root / "state",
    ]
    
    print(f"Setting up project structure at: {project_root}")
    
    all_success = True
    for dir_path in required_dirs:
        if not ensure_directory(dir_path):
            all_success = False
        else:
            print(f"  Created/Verified: {dir_path}")
    
    # Initialize README
    readme_content = "Project: Predicting Molecular Properties from TDA"
    if not initialize_readme(project_root, readme_content):
        all_success = False
    else:
        print(f"  Created: {project_root / 'README.md'}")
    
    if all_success:
        print("Project structure setup complete.")
        return 0
    else:
        print("Project structure setup failed.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
