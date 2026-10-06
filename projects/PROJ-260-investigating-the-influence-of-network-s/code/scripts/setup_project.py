import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the project.
    Implements T001a (Data Directories) and T001b (Output Directories).
    """
    # Define project root (assuming this script is in code/scripts/)
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # T001a: Data directories
    data_dirs = [
        "data/raw",
        "data/derived",
        "data/derived/topology",
        "data/derived/vdos",
        "data/derived/reference",
        "data/derived/correlation",
        "data/metadata",
    ]
    
    # T001b: Output directories
    output_dirs = [
        "outputs",
        "outputs/figures",
        "outputs/reports",
    ]
    
    # Create all directories
    all_dirs = [project_root / d for d in data_dirs + output_dirs]
    created_count = 0
    for d in all_dirs:
        d.mkdir(parents=True, exist_ok=True)
        created_count += 1
        print(f"Created directory: {d.relative_to(project_root)}")
    
    print(f"\nSuccessfully created {created_count} directories.")
    return all_dirs

def main():
    """Entry point for the script."""
    print("Initializing project directory structure...")
    create_directories()
    print("Directory structure initialization complete.")

if __name__ == "__main__":
    main()
