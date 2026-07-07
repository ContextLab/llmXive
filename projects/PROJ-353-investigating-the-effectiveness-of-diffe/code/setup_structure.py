import os
import sys
from pathlib import Path

def main():
    """
    Creates the foundational project directory structure.
    Ensures code/, tests/, and data/ subdirectories exist.
    """
    project_root = Path(__file__).parent.parent
    
    directories = [
        project_root / "code",
        project_root / "tests",
        project_root / "data" / "raw",
        project_root / "data" / "logs",
        project_root / "data" / "analysis",
        project_root / "data" / "figures",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {directory.relative_to(project_root)}")
        else:
            print(f"Directory already exists: {directory.relative_to(project_root)}")

    # Ensure __init__.py files exist for python packages
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "tests" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created package init: {init_file.relative_to(project_root)}")
        
    # Create .gitkeep files in data directories to prevent git from ignoring them
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "logs",
        project_root / "data" / "analysis",
        project_root / "data" / "figures",
    ]
    
    for data_dir in data_dirs:
        gitkeep = data_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in: {data_dir.relative_to(project_root)}")

    print(f"Project structure verification complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())