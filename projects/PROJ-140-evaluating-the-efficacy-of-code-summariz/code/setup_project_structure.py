import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the project directory structure as defined in T001.
    This script ensures all required folders exist on disk.
    """
    base_path = Path.cwd()
    
    # Define all required directories relative to the project root
    directories = [
        "code/data_prep",
        "code/analysis",
        "code/utils",
        "code/tests",
        "data/defects4j",
        "data/summaries",
        "data/interaction_logs",
        "data/analysis_results",
        "data/consent",
        "state/projects/PROJ-140-evaluating-the-efficacy-of-code-summariz"
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Creating project structure in: {base_path}")
    
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {dir_path}")
            created_count += 1
        else:
            print(f"Exists:  {dir_path}")
            skipped_count += 1
    
    print(f"\nProject structure setup complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories skipped (already exist): {skipped_count}")
    
    return True

if __name__ == "__main__":
    create_directories()