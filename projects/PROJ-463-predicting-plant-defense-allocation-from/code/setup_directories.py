"""
Script to create the project directory structure.
This script is idempotent and safe to run multiple times.
"""
import os
import sys
from pathlib import Path

# Ensure we can import from the code directory
code_root = Path(__file__).parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils.setup_directories import setup_data_directories, main as setup_main

def create_directory_structure(base_path: Path) -> None:
    """
    Create the standard project directory structure.
    
    Args:
        base_path: The root path of the project.
    """
    dirs = [
        "src",
        "src/utils",
        "src/data",
        "src/analysis",
        "src/cli",
        "src/models",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data",
        "data/raw",
        "data/processed",
        "data/traits",
        "data/manifests",
        "data/synthetic",
        "figures",
        "docs",
        "configs",
        "logs",
    ]

    for dir_path in dirs:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create __init__.py in Python packages
        if dir_path.startswith("src") or dir_path.startswith("tests"):
            init_file = full_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()

    print(f"Created directory structure at: {base_path}")

def main():
    """Main entry point for the script."""
    # Determine the project root (parent of 'code')
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    print(f"Project root detected at: {project_root}")
    
    # Create standard directories
    create_directory_structure(project_root)
    
    # Run the specific data directory setup logic from utils
    setup_main()
    
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
