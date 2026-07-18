"""
Module to initialize .gitkeep files in all empty directories.
Implements Task T001c: Create .gitkeep files in all empty directories.
"""
import os
import sys

def initialize_gitkeeps():
    """
    Traverses the project directory structure and ensures every directory
    contains a .gitkeep file. This prevents Git from ignoring empty directories.
    """
    root_dir = os.getcwd()

    # Define the directories to check
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/visualizations",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0
    existing_count = 0

    for dir_name in directories:
        dir_path = os.path.join(root_dir, dir_name)
        
        if not os.path.isdir(dir_path):
            print(f"Warning: Directory does not exist, skipping: {dir_path}")
            continue

        gitkeep_path = os.path.join(dir_path, ".gitkeep")

        if not os.path.exists(gitkeep_path):
            # Create an empty .gitkeep file
            with open(gitkeep_path, 'w') as f:
                f.write("# This file ensures the directory is tracked by Git.\n")
            print(f"Created .gitkeep in: {dir_path}")
            created_count += 1
        else:
            existing_count += 1

    print(f"Gitkeep setup complete. Created: {created_count}, Existing: {existing_count}")
    return True

if __name__ == "__main__":
    initialize_gitkeeps()
