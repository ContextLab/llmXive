"""
Project Structure Initialization Script for PROJ-212.

This script creates the required directory hierarchy for the network
synchronization research project as specified in the implementation plan.

Target Structure:
- src/ (source code)
- tests/ (test suites)
- data/ (raw and processed data)
  - data/raw/
  - data/processed/
- results/ (simulation and analysis outputs)
- state/ (intermediate state and flags)
"""
import os
from pathlib import Path


def main():
    """Create the project directory structure."""
    # Define the root directory for this project
    # The script is expected to be run from the project root:
    # projects/PROJ-212-exploring-the-impact-of-network-structur/code/
    # but the structure should be created relative to the project root.
    # We assume the script is run from the 'code' directory, so we go up one level
    # to find the project root, or we create the structure relative to the current
    # directory if that is the intended project root.
    #
    # Per task description: "projects/PROJ-212-exploring-the-impact-of-network-structur/code/"
    # The task asks to create structure per plan. The plan usually implies relative to the
    # project root. Let's assume the script is run from the project root or we target
    # the 'code' directory's parent if we are inside 'code'.
    #
    # However, looking at the existing file `code/setup_project_structure.py`, it seems
    # this file IS the implementation of T001.
    # The task says: "Create project structure ... by executing: mkdir -p ..."
    # We will create the directories relative to the current working directory
    # to ensure they exist where the rest of the code expects them.
    # Based on the file paths provided in the prompt (e.g., code/src/...),
    # the structure should be created inside the 'code' directory or the 'code'
    # directory itself is the root for 'src', 'tests', etc.
    #
    # Re-reading the task: "Create project structure per implementation plan
    # (`projects/PROJ-212-exploring-the-impact-of-network-structur/code/`) by executing:
    # `mkdir -p src tests data results data/raw data/processed state`."
    #
    # This implies the directories `src`, `tests`, `data`, etc. are to be created
    # inside the `code` directory.
    
    base_dir = Path.cwd()
    
    directories = [
        "src",
        "tests",
        "data",
        "results",
        "state",
        "data/raw",
        "data/processed",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")
    return 0


if __name__ == "__main__":
    exit(main())