"""
Script to initialize the project directory structure for PROJ-227.
Creates the required folders for data, code, tests, and state management.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to the script location or CWD
    # The task specifies paths relative to the project root.
    # We assume the script is run from the project root or the script determines the root.
    # Based on the task description, the root is likely the current working directory
    # where the project was initialized, or we create a specific subdirectory if implied.
    # However, the task says: "Create project directory structure: projects/PROJ-227..."
    # This implies the root of the repo is the parent of "projects".
    
    # Let's assume we are running from the repository root.
    # If the script is in code/, we need to go up two levels to reach repo root?
    # Or we just create relative to CWD. The task description implies:
    # "projects/PROJ-227-assessing-the-trade-offs-between-static-/" is the project folder.
    
    project_name = "PROJ-227-assessing-the-trade-offs-between-static-"
    base_path = Path("projects") / project_name
    
    required_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "state",
        base_path / "code",
        base_path / "tests",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
        base_path / "tests" / "contract",
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {dir_path}")
            created_count += 1
        else:
            print(f"Exists: {dir_path}")
    
    print(f"Setup complete. Created {created_count} new directories.")
    
    # Verification step: List the tree
    print("\n--- Directory Verification (ls -R) ---")
    if base_path.exists():
        # Walk and print
        for root, dirs, files in os.walk(base_path):
            level = root.replace(str(base_path), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f'{subindent}{file}')
    else:
        print(f"Error: Base path {base_path} does not exist.")
        sys.exit(1)

if __name__ == "__main__":
    main()