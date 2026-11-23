"""
Script to create project directory structure and init files.
This script is executed to ensure the required directory tree exists.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the required directory structure."""
    root = Path(__file__).parent
    
    # Define directories to create
    dirs = [
        root / "data" / "raw",
        root / "data" / "interim",
        root / "data" / "processed",
        root / "code",
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "reports",
    ]
    
    created = []
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))
        else:
            # Ensure they are directories
            if not d.is_dir():
                raise RuntimeError(f"{d} exists but is not a directory")
    
    return created

def create_init_files():
    """Create __init__.py files in code/ and tests/ if missing."""
    root = Path(__file__).parent
    
    init_files = [
        root / "code" / "__init__.py",
        root / "tests" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            # Create a minimal docstring
            init_file.write_text(
                f'"""\nProject: PROJ-216-exploring-the-relationship-between-brain\nModule: {init_file.parent.name}\n"""\n'
            )
            print(f"Created: {init_file}")
        else:
            print(f"Exists: {init_file}")

def main():
    """Main entry point."""
    print("Creating directory structure...")
    created_dirs = create_directories()
    if created_dirs:
        print(f"Created directories: {created_dirs}")
    else:
        print("All directories already exist.")
    
    print("\nCreating __init__.py files...")
    create_init_files()
    
    print("\nSetup complete.")

if __name__ == "__main__":
    main()