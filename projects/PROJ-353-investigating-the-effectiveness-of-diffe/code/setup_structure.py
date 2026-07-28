"""
Project Structure Initialization Script.
Creates the required directory hierarchy for the research pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard project directories."""
    root = Path(__file__).parent.parent
    
    directories = [
        root / "code",
        root / "tests",
        root / "data" / "raw",
        root / "data" / "logs",
        root / "data" / "analysis",
        root / "data" / "figures",
        root / "specs",
        root / "contracts",
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(root)}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path.relative_to(root)}")
    
    # Create __init__.py files if missing
    init_files = [
        root / "code" / "__init__.py",
        root / "tests" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.write_text("# Package initialization\n")
            print(f"Created init file: {init_file.relative_to(root)}")
            created_count += 1

    # Create .gitkeep files for data directories to ensure they are tracked
    data_dirs = [
        root / "data" / "raw",
        root / "data" / "logs",
        root / "data" / "analysis",
        root / "data" / "figures",
    ]
    
    for data_dir in data_dirs:
        keep_file = data_dir / ".gitkeep"
        if not keep_file.exists():
            keep_file.write_text("# Keep directory in git\n")
            print(f"Created .gitkeep: {keep_file.relative_to(root)}")
            created_count += 1

    if created_count == 0:
        print("Project structure already exists. Nothing to do.")
    else:
        print(f"Successfully created/verified {created_count} items.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
