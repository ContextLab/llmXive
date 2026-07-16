import os
import sys

def main():
    """
    Creates the project directory structure per the implementation plan.
    
    Required directories:
    - code/
    - data/raw/
    - data/interim/
    - data/processed/
    - tests/
    
    This script ensures all necessary folders exist to support the pipeline.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define relative paths to create
    directories = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "tests"
    ]
    
    created_count = 0
    for rel_path in directories:
        full_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
