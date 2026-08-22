import os
import sys
from typing import List

def create_directories() -> None:
    """
    Create the complete project directory structure for PROJ-485.
    
    This includes:
    - code/ and its subdirectories (ingest, features, models, viz, utils)
    - tests/
    - data/ and its subdirectories (raw, processed, artifacts)
    - state/
    
    Also creates __init__.py files to form Python packages.
    """
    # Define all required directories relative to project root
    required_dirs = [
        # Code structure
        "code",
        "code/ingest",
        "code/features",
        "code/models",
        "code/viz",
        "code/utils",
        
        # Test structure
        "tests",
        
        # Data structure
        "data",
        "data/raw",
        "data/processed",
        "data/artifacts",
        
        # State structure
        "state",
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create __init__.py files for Python packages
    init_files = []
    
    # code/ subdirectories
    code_subdirs = ["ingest", "features", "models", "viz", "utils"]
    for subdir in code_subdirs:
        init_path = os.path.join("code", subdir, "__init__.py")
        init_files.append(init_path)
        
    # tests/
    init_files.append(os.path.join("tests", "__init__.py"))
    
    # code/ itself
    init_files.append(os.path.join("code", "__init__.py"))
    
    for init_path in init_files:
        if not os.path.exists(init_path):
            with open(init_path, 'w') as f:
                f.write("# Auto-generated package initialization file\n")
            print(f"Created package init: {init_path}")
        else:
            print(f"Init file already exists: {init_path}")
    
    print(f"\nProject structure setup complete.")
    print(f"Created {created_count} new directories.")
    print(f"Created {len([f for f in init_files if not os.path.exists(f)])} new __init__.py files.")

def main() -> None:
    """Main entry point for directory setup."""
    print("Setting up project directory structure for PROJ-485...")
    create_directories()
    print("Done.")

if __name__ == "__main__":
    main()
