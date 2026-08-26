"""
Project Structure Initialization Script.
Creates the required directory tree for the llmXive research pipeline.
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the base path relative to the script location (project root)
    base_dir = Path(__file__).parent.parent.resolve()
    
    # Define required directories relative to project root
    dirs = [
        "code",
        "code/src",
        "code/tests",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
        "specs/001-exploring-the-relationship-between-code"
    ]
    
    created_count = 0
    for dir_path in dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {full_path}")
    
    print(f"Directory structure setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()