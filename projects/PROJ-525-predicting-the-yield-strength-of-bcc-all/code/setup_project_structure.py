"""
Task T001: Create project structure.
Creates the required directory tree for the llmXive science pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    # Define the root directory (current working directory or project root)
    root = Path(".")
    
    # Define the required directories relative to the root
    # Based on tasks.md: "mkdir -p data/raw data/processed data/logs code tests reports state"
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/logs",
        "code",
        "tests",
        "reports",
        "state"
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
            if full_path.is_dir():
                print(f"Directory already exists: {full_path}")
                existing_count += 1
            else:
                print(f"ERROR: Path exists but is not a directory: {full_path}", file=sys.stderr)
                sys.exit(1)
    
    print(f"Project structure setup complete. Created: {created_count}, Existing: {existing_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
