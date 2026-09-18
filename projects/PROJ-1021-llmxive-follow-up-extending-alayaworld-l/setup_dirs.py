"""
Script to create the required directory structure and initialize empty __init__.py files.
This implements task T001a.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DIR = PROJECT_ROOT / "projects" / "PROJ-1021-llmxive-follow-up-extending-alayaworld-l"

# Directories to create
dirs_to_create = [
    BASE_DIR / "code",
    BASE_DIR / "data",
    BASE_DIR / "tests",
    BASE_DIR / "config",
    BASE_DIR / "docs",
]

# Files to create (empty __init__.py in specific dirs)
init_files = [
    BASE_DIR / "code" / "__init__.py",
    BASE_DIR / "tests" / "__init__.py",
    BASE_DIR / "config" / "__init__.py",
]

def main():
    print(f"Creating directory structure for project: {BASE_DIR.name}")
    
    # Create directories
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created directory: {dir_path.relative_to(PROJECT_ROOT)}")
    
    # Create __init__.py files
    for file_path in init_files:
        # Ensure parent exists (it should from the loop above)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.write_text("")
            print(f"  Created empty file: {file_path.relative_to(PROJECT_ROOT)}")
        else:
            print(f"  File already exists: {file_path.relative_to(PROJECT_ROOT)}")

    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()