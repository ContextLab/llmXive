import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the standard project directory structure for the llmXive pipeline.
    This function ensures all required directories exist, creating them if necessary.
    """
    base_dir = Path(".")
    
    # Define the required directory structure relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs",
        "state"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")
    return True

def main():
    """
    Entry point for the project structure setup script.
    """
    try:
        create_structure()
        return 0
    except Exception as e:
        print(f"Error creating project structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
