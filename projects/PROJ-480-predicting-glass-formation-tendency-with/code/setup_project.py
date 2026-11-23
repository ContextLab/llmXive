import os
import sys
from pathlib import Path

def create_directories():
    """Create the project directory structure as per T001."""
    # Define the root directory (current working directory or project root)
    root = Path.cwd()
    
    # Define all required directories relative to root
    directories = [
        "src/data",
        "src/models",
        "src/reports",
        "src/cli",
        "src/lib",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "state",
        "reports"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nTotal directories created: {created_count}")
    print(f"Project structure setup complete at: {root}")
    return True

def main():
    """Entry point for the project setup script."""
    try:
        success = create_directories()
        if success:
            print("SUCCESS: Project structure created successfully.")
            sys.exit(0)
        else:
            print("FAILURE: Project structure creation failed.")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()