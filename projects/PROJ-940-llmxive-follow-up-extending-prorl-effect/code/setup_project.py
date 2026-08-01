"""
Script to create the project directory structure and placeholder files.
This script is idempotent and safe to run multiple times.
"""
import os
import sys

def create_structure():
    # Define the root relative to where the script is run (assuming project root)
    # The paths in tasks.md are relative to the project root.
    # We will create them relative to the current working directory.
    base_dir = os.getcwd()
    
    directories = [
        "src",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "results"
    ]
    
    files = [
        ("src", "__init__.py"),
        ("tests", "__init__.py"),
        ("tests/unit", "__init__.py"),
        ("tests/integration", "__init__.py"),
        ("data/raw", ".gitkeep"),
        ("data/processed", ".gitkeep"),
        ("results", ".gitkeep")
    ]

    print(f"Creating project structure in: {base_dir}")

    # Create directories
    for d in directories:
        path = os.path.join(base_dir, d)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Created directory: {d}")
        else:
            print(f"Directory exists: {d}")

    # Create files
    for dir_path, filename in files:
        full_path = os.path.join(base_dir, dir_path, filename)
        if not os.path.exists(full_path):
            # Ensure directory exists first
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                if filename == "__init__.py":
                    if dir_path == "src":
                        f.write('"""llmXive ProRL Zero-Shot Recommendation Pipeline."""\n')
                    elif "tests" in dir_path:
                        f.write('"""Test suite for llmXive ProRL Zero-Shot Recommendation Pipeline."""\n')
                    else:
                        f.write('"""\n')
                else:
                    # .gitkeep
                    f.write(".gitkeep\n")
            print(f"Created file: {full_path}")
        else:
            print(f"File exists: {full_path}")

    print("Project structure setup complete.")

if __name__ == "__main__":
    create_structure()