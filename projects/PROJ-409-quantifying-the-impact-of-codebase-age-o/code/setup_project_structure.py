"""
Project structure setup script for llmXive research pipeline.
Creates the required directory hierarchy for data, code, and tests.
"""
import os
import sys
from pathlib import Path

def create_directory_structure():
    """
    Creates the standard directory structure for the project.
    Returns a list of created paths.
    """
    # Define the root directory (current working directory or project root)
    # We assume this script is run from the project root
    root = Path.cwd()

    # Define all required directories relative to root
    directories = [
        # Code directories
        "code",
        "code/extraction",
        "code/inference",
        "code/analysis",
        "code/utils",
        
        # Data directories
        "data/raw",
        "data/extracted",
        "data/aggregated",
        "data/results",
        "data/models",
        
        # Test directories
        "tests/unit",
        "tests/integration",
    ]

    created_paths = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    return created_paths

def main():
    """Main entry point for the script."""
    print("Setting up project directory structure...")
    created = create_directory_structure()
    print(f"\nTotal directories created/verified: {len(created)}")
    
    # Verify the structure by listing the root contents
    root = Path.cwd()
    print("\nCurrent project structure:")
    for item in sorted(root.iterdir()):
        if item.is_dir():
            print(f"  {item.name}/")
            # List immediate subdirectories
            for subitem in sorted(item.iterdir()):
                if subitem.is_dir():
                    print(f"    {subitem.name}/")
                    
    return 0

if __name__ == "__main__":
    sys.exit(main())