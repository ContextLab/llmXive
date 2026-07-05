"""
Project Directory Initialization Script.

This script creates the required directory structure for the llmXive
research pipeline, including code/, data/, tests/, and specs/ directories,
along with all necessary subdirectories for data storage and processing.

Usage:
    python code/setup_dirs.py
"""
import os
from pathlib import Path


def setup_directories():
    """
    Create the complete project directory structure.
    
    Creates the following directories relative to the project root:
    - code/ (main source code)
      - code/data/
      - code/analysis/
      - code/viz/
      - code/utils/
    - data/
      - data/raw/ (raw downloaded data)
      - data/processed/ (cleaned, merged data)
    - tests/
      - tests/unit/
      - tests/integration/
      - tests/contract/
    - specs/
      - specs/001-csa-food-security/
    - state/ (for checksums and state tracking)
    
    Returns:
        Path: The project root directory path.
    """
    # Determine project root (parent of code/ directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    # Define all directories to create
    directories = [
        # Main directories
        project_root / "code",
        project_root / "data",
        project_root / "tests",
        project_root / "specs",
        
        # Code sub-packages
        project_root / "code" / "data",
        project_root / "code" / "analysis",
        project_root / "code" / "viz",
        project_root / "code" / "utils",
        
        # Data subdirectories
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        
        # Test subdirectories
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
        
        # Specs subdirectories
        project_root / "specs" / "001-csa-food-security",
        
        # State directory for checksums
        project_root / "state",
    ]
    
    # Create directories
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {dir_path.relative_to(project_root)}")
        else:
            print(f"Exists:  {dir_path.relative_to(project_root)}")
    
    print(f"\nDirectory setup complete. Created {created_count} new directories.")
    print(f"Project root: {project_root}")
    
    return project_root


if __name__ == "__main__":
    setup_directories()