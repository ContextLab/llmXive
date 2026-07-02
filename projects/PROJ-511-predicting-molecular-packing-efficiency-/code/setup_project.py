import os
import sys

def create_directories():
    """
    Creates the required project directory structure for the molecular packing efficiency project.
    
    Directories created:
    - code/
    - data/
    - data/raw_cif/
    - models/
    - results/
    - contracts/
    - specs/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    directories = [
        "code",
        "data",
        "data/raw_cif",
        "models",
        "results",
        "contracts",
        "specs"
    ]
    
    created_count = 0
    for directory in directories:
        full_path = os.path.join(base_dir, directory)
        try:
            os.makedirs(full_path, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        except Exception as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            return False
    
    print(f"Successfully created {created_count}/{len(directories)} directories.")
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
