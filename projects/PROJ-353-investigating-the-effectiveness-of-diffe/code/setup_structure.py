"""
Project structure initialization script.
Creates the required directory hierarchy for the llmXive research pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure.
    Creates code/, tests/, data/ (with subdirs), and specs/ if they don't exist.
    """
    base_dir = Path(__file__).parent.parent
    
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/logs",
        "data/analysis",
        "specs",
        "figures"
    ]
    
    created = []
    for d in directories:
        path = base_dir / d
        if not path.exists():
            path.mkdir(parents=True)
            created.append(str(path.relative_to(base_dir)))
            print(f"Created directory: {path}")
        else:
            print(f"Directory exists: {path}")
    
    # Create __init__.py files to make them packages
    package_dirs = ["code", "tests", "data"]
    for d in package_dirs:
        path = base_dir / d / "__init__.py"
        if not path.exists():
            path.write_text(f"# {d} package\n")
            print(f"Created {path}")
    
    # Create .gitkeep files in data subdirectories to ensure they are tracked
    data_subdirs = ["data/raw", "data/logs", "data/analysis"]
    for d in data_subdirs:
        path = base_dir / d / ".gitkeep"
        if not path.exists():
            path.write_text(f"# {d} directory\n")
            print(f"Created {path}")
    
    if not created:
        print("All directories already exist.")
    else:
        print(f"Successfully created {len(created)} directories.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())