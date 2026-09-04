import os
import sys
from pathlib import Path

def main():
    """
    Creates the directory structure for project PROJ-815-llmxive-follow-up-extending-intern-atlas.
    Ensures 'code/' and 'data/' are direct subdirectories of the project root, not nested.
    """
    # Define the project root relative to the script location or current working directory
    # The task specifies the root as: projects/PROJ-815-llmxive-follow-up-extending-intern-atlas
    # We assume the script is run from the repository root or the project root context.
    # To be safe, we construct the path relative to the current working directory.
    
    project_root = Path("projects/PROJ-815-llmxive-follow-up-extending-intern-atlas")
    
    # Define the required directories
    # Note: The task requires 'code/' and 'data/' to be direct subdirectories of the project root.
    # The brace expansion in the task description implies:
    # code/data, code/utils, code/models, code/analysis
    # data/raw, data/processed, data/cache
    # tests/unit, tests/integration
    # paper/results, state
    
    directories = [
        project_root / "code" / "data",
        project_root / "code" / "utils",
        project_root / "code" / "models",
        project_root / "code" / "analysis",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "cache",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "paper" / "results",
        project_root / "state",
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Verify the structure
    print(f"\nProject structure created/verified at: {project_root.absolute()}")
    print(f"Total directories processed: {len(directories)}")
    print(f"New directories created: {created_count}")
    
    # List the top-level structure to confirm 'code' and 'data' are siblings
    if project_root.exists():
        print("\nTop-level contents:")
        for item in sorted(project_root.iterdir()):
            print(f"  {item.name}/")

if __name__ == "__main__":
    main()