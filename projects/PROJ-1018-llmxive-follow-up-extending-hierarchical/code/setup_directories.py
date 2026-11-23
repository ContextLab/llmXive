import os
import sys

def create_directories():
    """
    Create the required project directory structure for llmXive follow-up.
    
    Creates the following directories relative to the project root:
    - src/
    - tests/
    - data/raw/
    - data/interim/
    - data/processed/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the project root based on the current working directory
    # In a real execution context, this would be the root of PROJ-1018
    base_path = os.getcwd()
    
    # Define the relative paths to create
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/interim",
        "data/processed"
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = os.path.join(base_path, dir_name)
        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
            except OSError as e:
                print(f"Error creating directory {full_path}: {e}")
                return False
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Successfully created {created_count} new directories.")
    return True

if __name__ == "__main__":
    # Execute the directory creation when run as a script
    success = create_directories()
    sys.exit(0 if success else 1)