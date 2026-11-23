"""
Project Structure Initialization Script.
Creates the required directory hierarchy for the llmXive science pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure as defined in plan.md."""
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the required directories relative to project root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests",
        "state"
    ]

    created_count = 0
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")

    print(f"\nProject structure initialization complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())