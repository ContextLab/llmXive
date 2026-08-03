"""
Project setup script to create the required directory structure.
"""
import os
from pathlib import Path
import sys

def create_directories():
    """Create the standard project directory structure."""
    base_dir = Path(__file__).parent
    
    directories = [
        "src",
        "src/utils",
        "src/data",
        "src/features",
        "src/models",
        "src/eval",
        "src/interpret",
        "src/report",
        "src/pipeline",
        "tests",
        "tests/unit",
        "tests/integration",
        "data",
        "data/raw",
        "data/processed",
        "results",
        "figures",
        "specs",
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create __init__.py for Python packages
        if dir_path.startswith("src") or dir_path.startswith("tests"):
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"Created {init_file}")
        
        print(f"Created directory: {full_path}")

def main():
    """Main entry point."""
    print("Setting up project directory structure...")
    create_directories()
    print("Project structure created successfully.")

if __name__ == "__main__":
    main()