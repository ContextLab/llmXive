import os
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in plan.md.
    This script ensures all required folders exist before other tasks run.
    """
    # Define the root directory (current working directory)
    root = Path(".")

    # Define the required directories relative to the root
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "tests",
        "results/paper_figures",
    ]

    created_count = 0
    existing_count = 0

    for dir_path in required_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            existing_count += 1

    print(f"\nDirectory setup complete.")
    print(f"  Created: {created_count}")
    print(f"  Existing: {existing_count}")
    print(f"  Total checked: {len(required_dirs)}")

    # Verification: List the structure
    print("\nVerified directory structure:")
    for dir_path in required_dirs:
        full_path = root / dir_path
        if full_path.exists():
            print(f"  [OK] {full_path}")
        else:
            print(f"  [FAIL] {full_path} (Missing)")
            return 1

    return 0

if __name__ == "__main__":
    exit(main())
