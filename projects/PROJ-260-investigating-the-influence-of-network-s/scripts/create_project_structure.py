"""
Script to create the project directory structure for PROJ-260.
Creates: src/, tests/, data/, outputs/, and their subdirectories.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the standard project directory structure."""
    root = Path(__file__).resolve().parent.parent
    
    directories = [
        # Source code
        "src",
        "src/models",
        "src/services",
        "src/lib",
        "src/cli",
        
        # Tests
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        
        # Data
        "data",
        "data/raw",
        "data/derived",
        "data/derived/topology",
        "data/derived/vdos",
        "data/derived/reference",
        "data/derived/correlation",
        "data/metadata",
        
        # Outputs
        "outputs",
        "outputs/reports",
        "outputs/figures",
        
        # Scripts (for utility scripts)
        "scripts",
    ]
    
    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path.relative_to(root)))
        else:
            # Verify it's a directory
            if not full_path.is_dir():
                print(f"Error: {dir_path} exists but is not a directory")
                return False
    
    if created:
        print("Created directories:")
        for d in sorted(created):
            print(f"  {d}/")
    else:
        print("All directories already exist.")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for dir_path in directories:
        full_path = root / dir_path
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")
    
    print("\nProject structure created successfully.")
    return True

def main():
    """Entry point for the script."""
    success = create_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
