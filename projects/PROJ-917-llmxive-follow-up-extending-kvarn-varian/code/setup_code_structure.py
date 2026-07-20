"""
Setup script to create the project directory structure.
Creates the main code/ directory and its required subdirectories:
- data_generation
- model_training
- simulation
- analysis
- tests
"""
import os
from pathlib import Path

def create_directories():
    """Create the code/ directory structure."""
    base_path = Path(__file__).resolve().parent.parent
    code_dir = base_path / "code"
    
    # Define required subdirectories
    subdirs = [
        "data_generation",
        "model_training",
        "simulation",
        "analysis",
        "tests"
    ]
    
    # Create directories
    for subdir in subdirs:
        dir_path = code_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {dir_path}")
    
    # Create __init__.py files to make them packages
    for subdir in subdirs:
        init_path = code_dir / subdir / "__init__.py"
        if not init_path.exists():
            init_path.touch()
            print(f"Created: {init_path}")
    
    print(f"Directory structure created successfully at {code_dir}")
    return code_dir

def main():
    """Main entry point."""
    create_directories()

if __name__ == "__main__":
    main()