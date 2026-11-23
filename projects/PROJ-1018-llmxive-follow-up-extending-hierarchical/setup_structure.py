"""
Script to initialize the project directory structure for llmXive follow-up.
Creates standard data science directories: src, tests, data/raw, data/interim, data/processed.
"""
import os
import sys

def main():
    # Define the base project root relative to the script location or current working directory
    # The task specifies the path relative to the project root.
    # Assuming this script is run from the root of the repo or the specific project folder.
    # We will create the directories relative to the current working directory.
    
    base_dir = os.getcwd()
    project_root = os.path.join(base_dir, "projects", "PROJ-1018-llmxive-follow-up-extending-hierarchical")
    
    # Ensure the project root exists first
    os.makedirs(project_root, exist_ok=True)
    
    # Define the directories to create relative to the project root
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/interim",
        "data/processed"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_name in directories:
        full_path = os.path.join(project_root, dir_name)
        if os.path.exists(full_path):
            print(f"[SKIP] Directory already exists: {full_path}")
            existing_count += 1
        else:
            os.makedirs(full_path, exist_ok=True)
            print(f"[CREATED] {full_path}")
            created_count += 1
    
    print(f"\nSummary: {created_count} directories created, {existing_count} already existed.")
    print(f"Project structure initialized at: {project_root}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
