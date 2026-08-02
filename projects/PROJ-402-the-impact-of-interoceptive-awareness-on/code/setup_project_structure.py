"""
Project Structure Initialization Script.

Creates the required directory structure and initialization files
for the llmXive automated science pipeline project.

Directories created:
- code/
- tests/
- data/
- data/raw/
- data/derived/
- data/audit/
- results/
- results/figures/
- specs/

Files created:
- __init__.py in code/, tests/, utils/
- .gitkeep in data/, results/, data/raw/, data/derived/, data/audit/, results/figures/
"""
import os
from pathlib import Path

# Define the base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Directories to create
DIRECTORIES = [
    "code",
    "tests",
    "data",
    "data/raw",
    "data/derived",
    "data/audit",
    "results",
    "results/figures",
    "specs",
    "code/utils"
]

# Files to create (relative to BASE_DIR)
INIT_FILES = [
    "code/__init__.py",
    "tests/__init__.py",
    "code/utils/__init__.py",
]

GITKEEP_FILES = [
    "data/.gitkeep",
    "results/.gitkeep",
    "data/raw/.gitkeep",
    "data/derived/.gitkeep",
    "data/audit/.gitkeep",
    "results/figures/.gitkeep",
]

def create_directories():
    """Create all required directories."""
    created = []
    for dir_path in DIRECTORIES:
        full_path = BASE_DIR / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
    return created

def create_init_files():
    """Create __init__.py files for Python packages."""
    created = []
    for file_path in INIT_FILES:
        full_path = BASE_DIR / file_path
        if not full_path.exists():
            # Create empty __init__.py
            full_path.touch()
            created.append(str(full_path))
    return created

def create_gitkeep_files():
    """Create .gitkeep files to preserve empty directories in git."""
    created = []
    for file_path in GITKEEP_FILES:
        full_path = BASE_DIR / file_path
        if not full_path.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
            created.append(str(full_path))
    return created

def main():
    """Main entry point to set up the project structure."""
    print("Initializing project structure...")
    
    dirs = create_directories()
    print(f"Created directories: {len(dirs)}")
    for d in dirs:
        print(f"  - {d}")
    
    inits = create_init_files()
    print(f"Created __init__.py files: {len(inits)}")
    for f in inits:
        print(f"  - {f}")
    
    gitkeeps = create_gitkeep_files()
    print(f"Created .gitkeep files: {len(gitkeeps)}")
    for f in gitkeeps:
        print(f"  - {f}")
    
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
