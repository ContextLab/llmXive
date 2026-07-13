"""
Script to initialize the project directory structure for PROJ-815.
This script creates the necessary folders for code, data, and tests.
"""
import os
import sys

# Define the project root relative to the script location or current working directory
# The task specifies paths relative to the project root.
# We will assume the script is run from the project root or adjust accordingly.
# To be safe, we calculate the project root as the parent of the 'code' directory if it exists,
# or simply use the current working directory if we are creating the root structure.

# Based on the task description: "mkdir -p projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/{...}"
# However, the constraint says: "All artifact paths are relative to the project root and MUST live under code/, data/..."
# And the task description implies we are setting up the structure *inside* the project.
# Let's assume the current working directory is the project root (PROJ-815-llmxive-follow-up-extending-intern-atlas).

# Directories to create
dirs = [
    "code/data",
    "code/models",
    "code/analysis",
    "code/utils",
    "data/raw",
    "data/processed",
    "tests/unit",
    "tests/integration"
]

def main():
    created_count = 0
    for dir_path in dirs:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
                print(f"Created directory: {dir_path}")
                created_count += 1
            else:
                print(f"Directory already exists: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
            sys.exit(1)
    
    print(f"Project structure initialization complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
