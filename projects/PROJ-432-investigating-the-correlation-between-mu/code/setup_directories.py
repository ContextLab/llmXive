import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure as defined in the implementation plan."""
    # Define the base directory (current working directory or explicit path)
    base_dir = Path(".").resolve()
    
    # Define the required directory structure relative to the project root
    # Note: The task description mentions 'src/', but the existing API surface shows files under 'code/'.
    # We will create the structure under 'code/' to align with the provided file paths (e.g., code/src/data/ingest.py).
    # The task also mentions 'data/raw', 'data/processed', etc.
    
    directories = [
        "code/src",
        "code/tests",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
        "code/logs",
        "code/config",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
