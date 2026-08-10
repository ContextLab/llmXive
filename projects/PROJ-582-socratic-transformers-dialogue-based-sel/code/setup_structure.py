"""
Script to create the directory structure for the Socratic Transformers project.
This script implements task T001a.
"""
import os
from pathlib import Path

def main():
    base_path = Path("projects/PROJ-582-socratic-transformers-dialogue-based-sel/code")
    
    # Define all required directories relative to the base path
    directories = [
        "",  # The base path itself
        "src",
        "src/data",
        "src/train",
        "src/eval",
        "src/analyze",
        "src/utils",
        "tests",
        "tests/contract",
        "tests/integration",
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

    print(f"\nTotal directories created: {created_count}")
    
    # Verification step as per task description
    print("\nVerifying directory structure:")
    for dir_name in directories:
        full_path = base_path / dir_name
        if full_path.exists() and full_path.is_dir():
            print(f"  [OK] {full_path}")
        else:
            print(f"  [FAIL] {full_path} (Missing)")
            return 1
    
    print("\nVerification complete. All directories exist.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())