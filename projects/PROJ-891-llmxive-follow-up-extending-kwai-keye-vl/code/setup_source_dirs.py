"""
Setup script to create the source directory structure for the llmXive project.

Creates the following directories relative to the project root:
- src/generators
- src/inference
- src/analysis
"""
import os
from pathlib import Path

def main():
    """Create the source directory structure."""
    # Define the base source directory
    src_root = Path("src")
    
    # Define the subdirectories to create
    subdirs = [
        "generators",
        "inference",
        "analysis"
    ]
    
    # Create each directory
    for subdir in subdirs:
        dir_path = src_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create __init__.py files to make them proper Python packages
    for subdir in subdirs:
        init_path = src_root / subdir / "__init__.py"
        init_path.touch(exist_ok=True)
        print(f"Created package init: {init_path}")
    
    print("Source directory structure setup complete.")

if __name__ == "__main__":
    main()
