"""
Script to initialize the project directory structure for PROJ-967.
Creates the required folders for data, code, tests, and results.
"""
import os
import sys

def create_directories(base_path: str) -> None:
    """
    Create the standard project directory structure.
    
    Args:
        base_path: The root path where directories will be created.
    """
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results",
        "projects/PROJ-967-llmxive-follow-up-extending-beyond-scala"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(base_path, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    if created_count == 0:
        print("No new directories were created.")
    else:
        print(f"Successfully created {created_count} directories.")

if __name__ == "__main__":
    # Determine the base path (current working directory or argument)
    if len(sys.argv) > 1:
        base = sys.argv[1]
    else:
        base = os.getcwd()

    print(f"Initializing project structure in: {base}")
    create_directories(base)
    print("Setup complete.")
