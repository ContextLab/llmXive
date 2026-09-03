import os
import sys
from pathlib import Path
from typing import List

def create_directories() -> List[Path]:
    """
    Creates the required project directory structure.
    Returns a list of created directory paths.
    """
    base_dirs = [
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
    created = []
    for d in base_dirs:
        path = Path(d)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)
        else:
            # Ensure we track existing ones for gitkeep creation
            created.append(path)
    return created

def create_gitkeep_files() -> int:
    """
    Creates .gitkeep files in all tracked directories to ensure
    version control tracks empty directories.
    Returns the count of .gitkeep files created/found.
    """
    dirs = [
        "code",
        "data",
        "data/raw",
        "data/raw/repos",
        "data/processed",
        "tests",
        "tests/unit",
        "tests/integration",
        "state",
        "logs"
    ]
    count = 0
    for d in dirs:
        path = Path(d)
        if path.exists():
            gitkeep = path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
            count += 1
    return count

def verify_structure() -> bool:
    """
    Verifies that all required directories exist and contain .gitkeep files.
    Returns True if structure is valid, False otherwise.
    """
    required_dirs = [
        "code", "code/utils", "data/raw", "data/raw/repos",
        "data/processed", "tests/unit", "tests/integration",
        "state", "logs"
    ]
    
    # Check directories
    for d in required_dirs:
        if not Path(d).exists():
            print(f"ERROR: Directory {d} does not exist.")
            return False

    # Check .gitkeep files in the top-level tracking dirs
    # The task verification command looks for .gitkeep in: code data tests state logs
    tracking_dirs = ["code", "data", "tests", "state", "logs"]
    found_gitkeeps = 0
    for d in tracking_dirs:
        gitkeep = Path(d) / ".gitkeep"
        if gitkeep.exists():
            found_gitkeeps += 1
    
    if found_gitkeeps != 5:
        print(f"ERROR: Expected 5 .gitkeep files in tracking dirs, found {found_gitkeeps}")
        return False

    print("Structure verification successful.")
    return True

def main():
    """
    Main entry point for setup script.
    """
    print("Creating project directories...")
    dirs = create_directories()
    print(f"Created/verified {len(dirs)} directories.")

    print("Creating .gitkeep files...")
    count = create_gitkeep_files()
    print(f"Created/verified {count} .gitkeep files.")

    print("Verifying structure...")
    if verify_structure():
        print("Setup complete.")
        sys.exit(0)
    else:
        print("Setup verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
