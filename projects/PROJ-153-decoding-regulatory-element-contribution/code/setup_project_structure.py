import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure:
    code/, tests/, data/, results/
    
    This implements the setup phase for the llmXive pipeline.
    """
    base_dir = Path(".")
    required_dirs = [
        "code",
        "tests",
        "data",
        "results",
        "data/raw",
        "data/processed",
        "results/figures",
        "results/tables",
        "specs"
    ]

    created_count = 0
    for dir_name in required_dirs:
        target_path = base_dir / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory exists: {target_path}")

    return created_count

def main():
    """Main entry point for project setup."""
    print("Initializing project directory structure...")
    created = create_directories()
    print(f"Setup complete. Created {created} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
