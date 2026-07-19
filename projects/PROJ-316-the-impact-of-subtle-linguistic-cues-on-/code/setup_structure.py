"""
Script to create the project directory structure and __init__.py files.
This corresponds to task T002.
"""
import os
from pathlib import Path

def setup_data_directories():
    """Create the required directory structure."""
    root = Path(__file__).parent
    
    # Define all required directories relative to the project root
    # Based on tasks.md T002 requirements
    directories = [
        "src",
        "src/extraction",
        "src/analysis",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "data/results",
        "contracts",
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))
        print(f"Created directory: {full_path}")
    
    return created_dirs

def create_init_files():
    """Create empty __init__.py files in all src/ and tests/ subfolders."""
    root = Path(__file__).parent
    
    # Directories that need __init__.py (src/ and tests/ tree)
    init_dirs = [
        "src",
        "src/extraction",
        "src/analysis",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created_files = []
    for dir_path in init_dirs:
        full_path = root / dir_path
        init_file = full_path / "__init__.py"
        
        # Create empty file (or overwrite if exists but empty)
        init_file.touch(exist_ok=True)
        created_files.append(str(init_file))
        print(f"Created __init__.py: {init_file}")
    
    return created_files

def main():
    """Main entry point for directory structure setup."""
    print("Setting up project directory structure for T002...")
    dirs = setup_data_directories()
    files = create_init_files()
    print(f"\nSetup complete. Created {len(dirs)} directories and {len(files)} __init__.py files.")
    print("All paths are relative to:", Path(__file__).parent)

if __name__ == "__main__":
    main()
