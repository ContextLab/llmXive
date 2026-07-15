"""
Setup Script for Project Directory Structure.

This script creates the necessary directory structure for the llmXive project
as defined in the task requirements.
"""
import os
import sys

def main():
    # Define the base project root relative to the script location or current dir
    # The task asks to create structure under the project root.
    # We will create the standard directories: code/, data/, tests/, contracts/
    
    directories = [
        "code",
        "code/generators",
        "code/metrics",
        "code/models",
        "code/agents",
        "code/evaluation",
        "code/utils",
        "code/contracts",
        "data/raw",
        "data/processed",
        "data/held_out",
        "data/interim",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "contracts",
        "figures",
        "docs",
        "scripts",
    ]

    created_count = 0
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    # Create placeholder files to ensure packages are recognized
    placeholders = [
        ("code/__init__.py", ""),
        ("tests/__init__.py", ""),
        ("contracts/__init__.py", ""),
        ("data/raw/.gitkeep", "# Raw data storage\n"),
        ("data/processed/.gitkeep", "# Processed data storage\n"),
        ("data/held_out/.gitkeep", "# Held-out data storage\n"),
        ("data/interim/.gitkeep", "# Interim data storage\n"),
    ]

    for file_path, content in placeholders:
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Created placeholder: {file_path}")
            created_count += 1
        else:
            print(f"Placeholder already exists: {file_path}")

    print(f"\nSetup complete. {created_count} items created/verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())