import os
import sys
from pathlib import Path
from typing import List

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "code",
    "code/utils",
    "data/raw",
    "data/raw/repos",
    "data/processed",
    "tests/unit",
    "tests/integration",
    "state",
    "logs"
]

def create_directories(base_path: Path) -> List[Path]:
    """
    Creates all required directories under the base path.
    Returns a list of created Path objects.
    """
    created_dirs = []
    for dir_name in REQUIRED_DIRS:
        target_dir = base_path / dir_name
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            created_dirs.append(target_dir)
        else:
            # Even if it exists, we ensure it's a directory
            if not target_dir.is_dir():
                raise NotADirectoryError(f"Path {target_dir} exists but is not a directory.")
    return created_dirs

def create_gitkeep_files(base_path: Path) -> List[Path]:
    """
    Creates .gitkeep files in all required directories to ensure they are tracked by git.
    Returns a list of created Path objects.
    """
    created_files = []
    for dir_name in REQUIRED_DIRS:
        target_dir = base_path / dir_name
        gitkeep_path = target_dir / ".gitkeep"
        if not gitkeep_path.exists():
          gitkeep_path.touch()
          created_files.append(gitkeep_path)
    return created_files

def verify_structure(base_path: Path) -> bool:
    """
    Verifies that all required directories and .gitkeep files exist.
    Returns True if the structure is complete, False otherwise.
    """
    all_good = True
    missing_dirs = []
    missing_gitkeeps = []

    for dir_name in REQUIRED_DIRS:
        target_dir = base_path / dir_name
        if not target_dir.exists() or not target_dir.is_dir():
            missing_dirs.append(dir_name)
            all_good = False
        
        gitkeep_path = target_dir / ".gitkeep"
        if not gitkeep_path.exists():
            missing_gitkeeps.append(dir_name)
            # We create it if missing to satisfy the task requirement of "creating .gitkeep files where needed"
            # But for verification logic, we note it was missing initially.
            # However, the task implies we create them. Let's assume we created them in the previous step.
            # If we are just verifying, we check existence.
            if not gitkeep_path.exists():
                 # This block is technically unreachable if create_gitkeep_files runs first
                 all_good = False

    if missing_dirs:
        print(f"Missing directories: {missing_dirs}")
    if missing_gitkeeps:
        print(f"Missing .gitkeep files in: {missing_gitkeeps}")
    
    return all_good

def main():
    """
    Main entry point for the setup structure script.
    Creates directories, creates .gitkeep files, and verifies the structure.
    """
    # Determine the base path (project root)
    # We assume the script is run from the project root or we find the git root
    current_path = Path.cwd()
    
    print(f"Setting up project structure in: {current_path}")
    
    # Step 1: Create directories
    print("Creating directories...")
    try:
        created = create_directories(current_path)
        if created:
            for d in created:
                print(f"  Created: {d}")
        else:
            print("  All directories already exist.")
    except Exception as e:
        print(f"Error creating directories: {e}")
        sys.exit(1)

    # Step 2: Create .gitkeep files
    print("Creating .gitkeep files...")
    try:
        created = create_gitkeep_files(current_path)
        if created:
            for f in created:
                print(f"  Created: {f}")
        else:
            print("  All .gitkeep files already exist.")
    except Exception as e:
        print(f"Error creating .gitkeep files: {e}")
        sys.exit(1)

    # Step 3: Verify structure
    print("Verifying structure...")
    if verify_structure(current_path):
        print("Project structure verification successful.")
        # Explicitly list the directories as requested by the task description
        print("\nVerified directories:")
        for dir_name in REQUIRED_DIRS:
            target = current_path / dir_name
            if target.exists():
                print(f"  [OK] {target}")
            else:
                print(f"  [FAIL] {target}")
        return 0
    else:
        print("Project structure verification FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
