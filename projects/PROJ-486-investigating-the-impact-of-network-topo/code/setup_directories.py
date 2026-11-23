import os
import sys

def create_directories():
    """
    Create the required project directory structure for the llmXive pipeline.
    
    Creates the following directories relative to the project root:
    - code/
    - data/
    - data/raw/
    - data/processed/
    - data/visualizations/
    - tests/
    - tests/unit/
    - tests/integration/
    - docs/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the directory structure relative to the project root
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/visualizations",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    created_count = 0
    failed_count = 0
    
    for dir_path in directories:
        try:
            # os.makedirs creates parent directories as needed
            # exist_ok=True prevents errors if directory already exists
            os.makedirs(dir_path, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        except OSError as e:
            print(f"Failed to create directory {dir_path}: {e}")
            failed_count += 1
    
    if failed_count > 0:
        print(f"\nWarning: {failed_count} directory(ies) failed to create.")
        return False
    
    print(f"\nSuccessfully created {created_count} directories.")
    return True

def main():
    """Entry point for directory creation script."""
    print("Initializing project directory structure...")
    success = create_directories()
    
    if success:
        print("Directory structure initialization complete.")
        sys.exit(0)
    else:
        print("Directory structure initialization encountered errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()
