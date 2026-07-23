import os
import sys
from pathlib import Path

def create_project_structure():
    """
    Creates the full directory tree and places a .gitkeep file in each
    to ensure they are committed and verifiable.
    """
    # Define all required directories relative to the project root
    # The script assumes it is run from the project root or passed the root path.
    # We use the current working directory as the root for this implementation.
    root = Path.cwd()

    directories = [
        "code",
        "data",
        "data/raw",
        "data/derived",
        "data/artifacts",
        "specs/001-llmxive-followup/contracts",
        "code/01_data_ingestion",
        "code/02_annotation_distillation",
        "code/03_execution",
        "code/04_analysis",
        "code/utils",
        "tests",
    ]

    created_count = 0
    kept_count = 0

    for dir_path_str in directories:
        dir_path = root / dir_path_str
        
        # Create the directory if it doesn't exist
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

        # Create .gitkeep file if it doesn't exist
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text("# Placeholder to ensure directory is tracked\n")
            kept_count += 1
            print(f"Created .gitkeep in: {dir_path}")
        else:
            print(f".gitkeep already exists in: {dir_path}")

    print(f"\nProject structure initialization complete.")
    print(f"Directories checked: {len(directories)}")
    print(f"New directories created: {created_count}")
    print(f"New .gitkeep files created: {kept_count}")

def main():
    create_project_structure()

if __name__ == "__main__":
    main()