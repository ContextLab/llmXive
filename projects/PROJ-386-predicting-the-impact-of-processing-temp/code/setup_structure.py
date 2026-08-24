"""
Project Structure Initialization Script.
Creates the required directory hierarchy for the llmXive science pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests",
        "state",
        "specs"
    ]

    created_count = 0
    for dir_name in required_dirs:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(root)}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path.relative_to(root)}")

    print(f"\nProject structure verification complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
