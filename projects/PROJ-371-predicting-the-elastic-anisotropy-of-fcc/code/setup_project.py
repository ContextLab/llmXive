import os
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in the implementation plan.
    This script ensures all necessary folders exist for the elastic anisotropy project.
    """
    # Define the project root relative to the script location (or current dir)
    # The task specifies paths relative to the project root.
    # We assume this script runs from the project root or we derive root from script dir.
    # To be safe and consistent with "stay inside project tree", we use relative paths
    # assuming the script is run from the root.
    
    root = Path(".")
    
    directories = [
        "src/data",
        "src/models",
        "src/utils",
        "src/cli",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "output"
    ]
    
    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Ensure it's a directory, not a file
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    # Create .gitkeep files in data directories to ensure they are tracked by git
    gitkeep_dirs = ["data/raw", "data/processed"]
    for dir_path in gitkeep_dirs:
        full_path = root / dir_path / ".gitkeep"
        full_path.touch(exist_ok=True)
        created.append(str(full_path))

    print(f"Project structure created/verified: {len(created)} items.")
    for item in created:
        print(f"  - {item}")

if __name__ == "__main__":
    main()