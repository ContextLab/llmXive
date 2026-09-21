"""
Project Structure Initialization Script for PROJ-443.
Creates the required directory hierarchy for the HEA Elastic Modulus project.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the standard project directory structure."""
    # Define the base directory (current working directory or project root)
    base_path = Path.cwd()
    
    # Define relative paths based on the task requirements
    # Note: The task asks for 'src/', 'tests/', 'data/raw/', etc.
    # However, the existing API surface shows code in 'code/' and 'src/' subdirectories.
    # To align with the existing API surface provided in the prompt (e.g., code/setup_environment.py),
    # we will create the structure relative to the 'code/' directory if it exists,
    # or assume the project root is the working directory and create 'code/' as the root for logic.
    #
    # Re-evaluating the prompt's existing API:
    # "code/setup_project.py" exists and imports "from setup_project import create_directories"
    # The task T002 asks for: src/, tests/, data/raw/, data/processed/, results/
    # The existing files (e.g., code/src/data/fetch_mp.py) suggest the structure is:
    # code/
    #   src/
    #   tests/
    #   data/
    #     raw/
    #     processed/
    #   results/
    #
    # We will create these directories under the current working directory,
    # assuming the script is run from the project root where 'code' is a sibling or
    # the script itself is inside 'code'.
    # Given the file path "code/setup_project.py", we assume the script runs from the project root.
    
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "results",
        "figures",
        "specs",
        "code/utils",
        "code/features",
        "code/models",
        "code/data",
        "code/pipeline",
        "code/eval",
        "code/interpret",
        "code/report",
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Initializing project structure at: {base_path}")
    
    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.is_dir() and not any(full_path.iterdir()):
                # Create a .gitkeep to ensure empty directories are tracked
                (full_path / ".gitkeep").touch()
                print(f"  Created: {dir_path}/")
                created_count += 1
            else:
                if full_path.exists():
                    print(f"  Exists: {dir_path}/")
                    skipped_count += 1
                else:
                    print(f"  Created: {dir_path}/")
                    created_count += 1
        except Exception as e:
            print(f"  Error creating {dir_path}: {e}")
            
    print(f"\nProject structure initialization complete.")
    print(f"  Created: {created_count} directories")
    print(f"  Skipped/Exists: {skipped_count} directories")
    
    return True

def main():
    """Entry point for the script."""
    try:
        create_directories()
        return 0
    except Exception as e:
        print(f"Fatal error during project setup: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
