"""
Script to create the required data directory structure for the llmXive project.

This script creates the following directories under the project root:
- data/raw: For raw dataset downloads (WISE, RISE, etc.)
- data/intermediate: For processed data and temporary files
- data/simulator_validation: For validation datasets and results
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the required data directory structure."""
    # Determine project root (assuming script is in code/scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "intermediate",
        project_root / "data" / "simulator_validation",
    ]
    
    created = []
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        created.append(str(dir_path.relative_to(project_root)))
        print(f"Created: {dir_path}")
    
    return created

def print_tree(base_path=None):
    """Print a tree representation of the data directory structure."""
    if base_path is None:
        base_path = Path(__file__).resolve().parent.parent.parent / "data"
    
    base_path = Path(base_path)
    if not base_path.exists():
        print(f"Error: {base_path} does not exist.")
        return
    
    print(f"Data directory structure at: {base_path}")
    for item in sorted(base_path.rglob("*")):
        if item.is_dir():
            print(f"  [DIR]  {item.relative_to(base_path)}")
        else:
            print(f"  [FILE] {item.relative_to(base_path)}")

def main():
    """Main entry point."""
    print("Setting up data directory structure...")
    created = create_directories()
    print(f"\nSuccessfully created {len(created)} directories.")
    print("\nDirectory tree:")
    print_tree()

if __name__ == "__main__":
    main()
