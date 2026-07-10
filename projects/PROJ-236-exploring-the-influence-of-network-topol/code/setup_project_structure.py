"""
Script to initialize the project directory structure for PROJ-236.
Creates all necessary directories for code, data, tests, and state management.
"""
import os
from pathlib import Path

def main():
    # Define the project root based on the current working directory context
    # The task implies running from the project root or a specific parent.
    # We will create paths relative to the current working directory (CWD).
    root = Path.cwd()

    # List of directories to create as per T001 specification
    directories = [
        "code/utils",
        "code/tests/unit",
        "code/tests/integration",
        "data/raw",
        "data/networks",
        "data/transport",
        "data/analysis",
        "plots",
        "state/projects",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nProject structure initialization complete. {created_count} new directories created.")

    # Verification: Assert all exist
    missing = []
    for dir_path in directories:
        if not (root / dir_path).exists():
            missing.append(dir_path)

    if missing:
        raise RuntimeError(f"Verification failed: The following directories were not created: {missing}")
    
    print("Verification passed: All required directories exist.")

if __name__ == "__main__":
    main()
