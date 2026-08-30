"""
Script to create the project directory structure for llmXive PROJ-754.

This script ensures the existence of all required directories as specified
in the implementation plan, including top-level folders and specific subdirectories.
"""
import os
import sys
from pathlib import Path

def get_project_root() -> Path:
    """Get the project root directory (parent of 'scripts' folder)."""
    # Assuming this script is located at code/scripts/create_project_structure.py
    # Project root is code/
    current_file = Path(__file__).resolve()
    scripts_dir = current_file.parent
    return scripts_dir.parent

def ensure_directory(dir_path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to the directory to create
        
    Returns:
        True if directory was created or already exists, False on error
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created/Verified: {dir_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to create {dir_path}: {e}")
        return False

def main():
    """Create the full project directory structure."""
    project_root = get_project_root()
    print(f"Project root: {project_root}")
    
    # Define all required directories relative to project root
    required_dirs = [
        # Top-level directories
        "src",
        "tests",
        "data",
        "reports",
        "docs",
        "scripts",
        "state",
        
        # src subdirectories
        "src/data",
        "src/analysis",
        "src/stats",
        "src/config",
        "src/utils",
        "src/entities",
        
        # tests subdirectories
        "tests/unit",
        "tests/integration",
        
        # Additional data subdirectories (for organization)
        "data/raw",
        "data/cleaned",
        "data/derived",
        "data/results",
        
        # Additional reports subdirectory
        "reports/figures",
        
        # Additional docs subdirectory
        "docs/api",
    ]
    
    success_count = 0
    failed_dirs = []
    
    for dir_str in required_dirs:
        dir_path = project_root / dir_str
        if ensure_directory(dir_path):
            success_count += 1
        else:
            failed_dirs.append(dir_str)
    
    print(f"\n{'='*60}")
    print(f"Directory creation summary:")
    print(f"  Total directories: {len(required_dirs)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {len(failed_dirs)}")
    
    if failed_dirs:
        print(f"\nFailed directories:")
        for d in failed_dirs:
            print(f"  - {d}")
        sys.exit(1)
    else:
        print("\n✓ All directories created successfully!")
        
        # List the created structure
        print(f"\nCreated directory tree:")
        print(project_root)
        for dir_str in required_dirs:
            print(f"└── {dir_str}")
        
        sys.exit(0)

if __name__ == "__main__":
    main()