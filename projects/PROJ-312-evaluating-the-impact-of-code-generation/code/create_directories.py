import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the project.
    Implements T001a: Create directory structure.
    """
    base_dir = Path("projects/PROJ-312-evaluating-the-impact-of-code-generation")
    
    # Define all required directories relative to the project root
    # Note: The task description lists 'code/', 'data/', etc. as top level, 
    # but the project structure convention in tasks.md (Phase 1) suggests 
    # they should be inside the project folder to keep the repo clean.
    # We will create them inside the project folder as per standard practice 
    # for this specific project ID.
    
    dirs_to_create = [
        base_dir / "code",
        base_dir / "data",
        base_dir / "tests",
        base_dir / "contracts",
        base_dir / "artifacts",
        base_dir / "state",
        # Subdirectories for data as per T008 (often run together or T008 is a sub-task of setup)
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "spot_check",
        base_dir / "tests" / "unit",
        base_dir / "tests" / "contract",
        base_dir / "tests" / "integration",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Directory creation complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())
