"""
Script to initialize the project directory structure for PROJ-843.
This script creates the required directories: code/, data/, and tests/
relative to the project root.
"""
import os
import sys

def main():
    # Define the directories to create relative to the current working directory (project root)
    # The task specifies the project root is projects/PROJ-843-llmxive-follow-up-extending-latent-spati/
    # We assume this script is run from that root.
    directories = [
        "code",
        "data",
        "tests"
    ]

    created_count = 0
    for dir_name in directories:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"Created directory: {dir_name}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_name}")

    # Create __init__.py files to make them packages
    for dir_name in directories:
        init_path = os.path.join(dir_name, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write(f'"""\n{dir_name} directory for PROJ-843.\n"""\n')
            print(f"Created {init_path}")

    if created_count == 0:
        print("No new directories created. Structure already exists.")
    else:
        print(f"Project structure initialized successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())