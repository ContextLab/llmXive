"""
Setup directory structure for the project.
Creates required directories under the project root.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required directory structure."""
    # Determine project root based on the current working directory context
    # The script is expected to be run from the project root:
    # projects/PROJ-498-investigating-the-relationship-between-n/
    project_root = Path.cwd()
    
    # Define the required directories relative to the project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/metrics",
        "data/trial_level",
        "code",
        "tests",
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            existing_count += 1
            print(f"Directory exists: {full_path}")
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
    
    print(f"\nDirectory setup complete. Created: {created_count}, Existing: {existing_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())