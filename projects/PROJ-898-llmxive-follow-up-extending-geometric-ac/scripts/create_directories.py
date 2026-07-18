"""
Script to ensure the required directory structure exists for the llmXive project.
This script creates 'code/', 'data/', and 'tests/' directories if they don't exist.
"""
import os
import sys

def main():
    """Create the required project directories."""
    directories = [
        "code",
        "data",
        "tests"
    ]

    created_count = 0
    existing_count = 0

    for directory in directories:
        if os.path.exists(directory):
            print(f"Directory '{directory}' already exists.")
            existing_count += 1
        else:
            os.makedirs(directory)
            print(f"Created directory: '{directory}'")
            created_count += 1

    # Create .gitkeep files to ensure directories are tracked by git
    gitkeep_files = [
        "code/.gitkeep",
        "data/.gitkeep",
        "tests/.gitkeep"
    ]

    for file_path in gitkeep_files:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                # Add a comment to explain the file's purpose
                f.write(f"# Git keep file for {os.path.dirname(file_path)}\n")
            print(f"Created .gitkeep file: '{file_path}'")
        else:
            print(f".gitkeep file '{file_path}' already exists.")

    print(f"\nSummary: {created_count} directories created, {existing_count} already existed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
