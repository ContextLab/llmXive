"""
Project initialization script.
Creates the required directory structure for the llmXive Equivalence Principle project.
"""
import os
import sys

def create_project_structure():
    """Create the directory structure defined in plan.md and tasks.md."""
    # Define the root directory (current working directory or specified path)
    root_dir = os.getcwd()
    
    # List of directories to create relative to root
    directories = [
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "code/tests",
        "contracts",
        "data/raw",
        "data/processed",
        "data/results",
        "docs",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(root_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path}")

    # Create __init__.py files to make directories packages where appropriate
    init_dirs = [
        "code",
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "code/tests",
    ]
    
    for dir_path in init_dirs:
        full_path = os.path.join(root_dir, dir_path, "__init__.py")
        if not os.path.exists(full_path):
            with open(full_path, "w") as f:
                f.write("# Package initialization\n")
            print(f"Created __init__.py in: {dir_path}")
            created_count += 1

    print(f"\nProject structure initialized. {created_count} items created/checked.")
    return created_count

if __name__ == "__main__":
    create_project_structure()
