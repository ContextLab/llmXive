"""
Script to create the required subdirectories for the project structure.
This implements task T001b: Create subdirectories code/, data/raw/, data/processed/, tests/, contracts/
INSIDE the projects/PROJ-160-investigating-the-impact-of-early-life-s/ directory.
"""
import os
import sys
from pathlib import Path

# Define the project root based on the task description
PROJECT_ID = "PROJ-160-investigating-the-impact-of-early-life-s"
BASE_DIR = Path("projects") / PROJECT_ID

# Define the required subdirectories relative to the project root
REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "tests",
    "contracts"
]

def main():
    """
    Creates the required subdirectories if they do not exist.
    Prints the status of each directory creation.
    """
    if not BASE_DIR.exists():
        print(f"Error: Base project directory {BASE_DIR} does not exist. "
              f"Please run T001a first to create the root directory.")
        sys.exit(1)

    print(f"Creating subdirectories inside {BASE_DIR}...")
    created_count = 0

    for dir_name in REQUIRED_DIRS:
        dir_path = BASE_DIR / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            if dir_path.is_dir():
                print(f"  [OK] Created: {dir_path}")
                created_count += 1
            else:
                print(f"  [FAIL] Path exists but is not a directory: {dir_path}")
        except OSError as e:
            print(f"  [ERROR] Failed to create {dir_path}: {e}")

    print(f"\nSummary: Successfully created {created_count}/{len(REQUIRED_DIRS)} directories.")
    
    # Verification: List the contents of the project root to prove existence
    print(f"\nVerification: Contents of {BASE_DIR}:")
    for item in sorted(BASE_DIR.iterdir()):
        print(f"  - {item.name}")

if __name__ == "__main__":
    main()
