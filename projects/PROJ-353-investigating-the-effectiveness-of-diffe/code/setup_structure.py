"""
Project structure initialization script.
Creates the required directory tree for the research pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure:
    - code/
    - tests/
    - data/raw/
    - data/logs/
    - data/analysis/
    """
    root = Path(__file__).parent.parent
    
    directories = [
        root / "code",
        root / "tests",
        root / "data" / "raw",
        root / "data" / "logs",
        root / "data" / "analysis",
    ]
    
    created = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created += 1
        else:
            print(f"Directory already exists: {directory}")
    
    # Create __init__.py files to ensure they are recognized as packages
    init_files = [
        root / "code" / "__init__.py",
        root / "tests" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.write_text('"""Auto-generated init file."""\n')
            print(f"Created init file: {init_file}")
            created += 1
        
    # Create .gitkeep files for data directories to ensure they are tracked
    gitkeep_files = [
        root / "data" / "raw" / ".gitkeep",
        root / "data" / "logs" / ".gitkeep",
        root / "data" / "analysis" / ".gitkeep",
    ]
    
    for gitkeep in gitkeep_files:
        if not gitkeep.exists():
            gitkeep.write_text('"""Directory for data artifacts."""\n')
            print(f"Created .gitkeep: {gitkeep}")
            created += 1
    
    print(f"Project structure initialization complete. Created {created} new items.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
