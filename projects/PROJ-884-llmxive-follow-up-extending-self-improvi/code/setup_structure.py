import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure for llmXive follow-up.
    Executes the mkdir command logic to ensure all required folders exist.
    """
    project_root = Path("projects/PROJ-884-llmxive-follow-up-extending-self-improvi")
    
    # Define all required directories
    directories = [
        "data/raw",
        "data/processed",
        "code/dataset",
        "code/symbolic",
        "code/bes",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = project_root / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure ready. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
