import os
import sys
from pathlib import Path

def main():
    """
    Creates the required directory structure for the llmXive project.
    This script ensures all necessary folders for code, tests, data, and outputs exist.
    """
    # Define the project root (assuming this script is in code/tools/)
    # We navigate up to the project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Define relative paths to create
    # Based on tasks.md and the project structure implied by existing files:
    # Code structure: src/services, src/models, src/utils, src/data-models (file or dir)
    # Test structure: tests/unit, tests/contract
    # Data structure: data/raw, data/filtered, data/scores
    # Output structure: outputs

    directories = [
        # Source directories
        "src/services",
        "src/models",
        "src/utils",
        "src/data-models", # Task T001e references this as a directory in the prompt, though T006 suggests a file. Creating as dir to be safe or ensuring parent exists.
        
        # Test directories
        "tests/unit",
        "tests/contract",
        
        # Data directories
        "data/raw",
        "data/filtered",
        "data/scores",
        
        # Output directories
        "outputs",
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1
            # Optional: verify it's a directory
            if not full_path.is_dir():
                print(f"WARNING: {full_path} exists but is not a directory!")

    print(f"\nDirectory setup complete.")
    print(f"Created: {created_count} new directories.")
    print(f"Existing: {existing_count} directories.")

    return 0

if __name__ == "__main__":
    sys.exit(main())