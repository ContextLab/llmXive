import os
from pathlib import Path

def main():
    """
    Creates the standard directory structure for the molecular toxicity project.
    This script ensures all required directories exist before pipeline execution.
    """
    # Define the project root relative to the script location
    # Assuming script is at code/scripts/
    script_dir = Path(__file__).resolve().parent
    code_root = script_dir.parent
    
    # Define directories to create
    directories = [
        code_root / "src",
        code_root / "tests",
        code_root / "data",
        code_root / "results",
        code_root / "models",
        code_root / "config",
        code_root / "docs",
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())
