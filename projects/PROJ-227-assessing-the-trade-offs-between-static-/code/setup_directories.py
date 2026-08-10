import os
from pathlib import Path

def main():
    """
    Creates the required project directory structure for PROJ-227.
    
    Directories created:
    - projects/PROJ-227-assessing-the-trade-offs-between-static-/data/raw/
    - projects/PROJ-227-assessing-the-trade-offs-between-static-/data/processed/
    - projects/PROJ-227-assessing-the-trade-offs-between-static-/state/
    - projects/PROJ-227-assessing-the-trade-offs-between-static-/code/
    - projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/
    """
    project_root = Path("projects/PROJ-227-assessing-the-trade-offs-between-static-")
    
    # Define the required subdirectories
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state",
        project_root / "code",
        project_root / "tests",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created: {directory}")
            created_count += 1
        else:
            print(f"Exists:  {directory}")
    
    if created_count > 0:
        print(f"Successfully created {created_count} new directories.")
    else:
        print("All required directories already exist.")

    return 0

if __name__ == "__main__":
    exit(main())
