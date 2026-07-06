"""
Script to initialize the project directory structure for the LLM Carbon Footprint study.
Creates the necessary folders for code, data (raw, processed, outputs), tests, and output.
"""
import os
import sys

# Define the directory structure relative to the project root
DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/outputs",
    "tests",
    "tests/unit",
    "tests/contract",
    "output",
    "figures",
    "specs",
]

def main():
    base_dir = os.getcwd()
    created_count = 0
    existing_count = 0

    print(f"Initializing project structure in: {base_dir}")

    for dir_path in DIRS:
        full_path = os.path.join(base_dir, dir_path)
        try:
            if not os.path.exists(full_path):
                os.makedirs(full_path)
                print(f"  Created: {dir_path}")
                created_count += 1
            else:
                print(f"  Exists:  {dir_path}")
                existing_count += 1
        except OSError as e:
            print(f"  Error creating {dir_path}: {e}")
            sys.exit(1)

    print(f"\nSetup complete. Created {created_count} directories, skipped {existing_count}.")

if __name__ == "__main__":
    main()
