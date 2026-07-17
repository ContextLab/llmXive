import os
from pathlib import Path

def main():
    """
    Creates the foundational directory structure for the llmXive project.
    This script ensures all required directories exist before data generation or simulation.
    """
    # Define the project root based on the task context
    # The task specifies paths relative to the project root.
    # We assume the script is run from the project root or the project root is the current directory.
    # To be safe, we define the base path as the current working directory if not specified otherwise,
    # but the task description implies a specific project folder structure.
    # Since the task asks to create directories IN `projects/PROJ-920-llmxive-follow-up-extending-masking-stal/`,
    # we will create them relative to the current working directory assuming it is the project root.
    # If the user runs this from inside the project folder, it works.
    
    base_path = Path(".")
    
    # Define the required directories
    directories = [
        "data/raw",
        "data/processed",
        "output/plots",
        "code",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Directory setup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()
