import os
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for PROJ-002.
    Directories created relative to the project root:
    - src/
    - tests/
    - config/
    - data/
    - results/
    - docs/
    """
    # Define the root as the current working directory (project root)
    root = Path.cwd()
    
    # Define required directories based on tasks.md and plan.md
    required_dirs = [
        "src",
        "tests",
        "config",
        "data",
        "results",
        "docs"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_name in required_dirs:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Ensure it is actually a directory if it exists
            if not dir_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {dir_path}")
            skipped_count += 1
    
    print(f"Project structure verification complete. Created: {created_count}, Skipped (existing): {skipped_count}")
    return True

if __name__ == "__main__":
    create_directories()
