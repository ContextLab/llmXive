import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure for the statistical analysis project.
    Implements T002a: Create Project Structure.
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the required directories relative to the project root
    directories = [
        "src/data",
        "src/models",
        "src/analysis",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            existing_count += 1
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories already existing: {existing_count}")
    print(f"Total directories managed: {created_count + existing_count}")
    
    return True

def main():
    """Main entry point for the setup script."""
    try:
        success = create_directories()
        if success:
            print("\nT002a: Project structure created successfully.")
            sys.exit(0)
        else:
            print("\nT002a: Project structure creation failed.")
            sys.exit(1)
    except Exception as e:
        print(f"\nT002a: Error during project structure creation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())