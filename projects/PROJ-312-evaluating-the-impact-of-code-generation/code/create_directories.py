import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the project.
    Implements Task T008: Create directory structure:
    data/raw/, data/processed/, data/spot_check/, artifacts/, tests/
    """
    # Define the project root relative to this script's location
    # Assuming the script is in code/, root is parent
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    # Define relative paths to create
    directories = [
        root_dir / "data" / "raw",
        root_dir / "data" / "processed",
        root_dir / "data" / "spot_check",
        root_dir / "artifacts",
        root_dir / "tests",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    # Also ensure the parent 'data' and 'tests' directories exist if they don't
    # (though mkdir with parents=True handles this, explicit check is fine)
    if not (root_dir / "data").exists():
        (root_dir / "data").mkdir(parents=True, exist_ok=True)
    
    if not (root_dir / "tests").exists():
        (root_dir / "tests").mkdir(parents=True, exist_ok=True)

    print(f"Directory structure verification complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())