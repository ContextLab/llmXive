"""
Directory structure setup utility for the alloy design project.
Creates the required directory hierarchy and placeholder files.
"""
import os
from pathlib import Path


def create_directory_structure(base_path: str = ".") -> None:
    """
    Create the required directory structure for the project.
    
    Args:
        base_path: The root directory where structure will be created.
    """
    root = Path(base_path)
    
    # Define all required directories
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs",
        "figures",
        "specs",
        "specs/001-multi-property-trade-offs",
    ]
    
    # Create directories
    created_dirs = []
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))
    
    # Create .gitkeep files in all directories to ensure they are tracked by git
    gitkeep_files = []
    for dir_path in directories:
        full_path = root / dir_path
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            gitkeep_files.append(str(gitkeep_path))
    
    # Log results
    print(f"Created {len(created_dirs)} directories:")
    for d in created_dirs:
        print(f"  - {d}")
    
    print(f"\nCreated {len(gitkeep_files)} .gitkeep placeholder files:")
    for f in gitkeep_files:
        print(f"  - {f}")


if __name__ == "__main__":
    create_directory_structure()