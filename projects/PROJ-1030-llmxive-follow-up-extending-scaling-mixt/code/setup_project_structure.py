import os
import sys
from pathlib import Path

def create_directories():
    """Create the project directory structure as defined in T001."""
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the required directories relative to the project root
    directories = [
        "code",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs/figures",
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
    
    return created_count

def main():
    """Entry point for the project structure setup script."""
    print("Initializing project structure for llmXive...")
    count = create_directories()
    print(f"Setup complete. {count} new directories created.")

if __name__ == "__main__":
    main()