import os
import sys

def create_data_directories():
    """
    Creates the required data directory structure:
    - data/raw/
    - data/processed/
    - data/results/
    
    Returns a list of created directory paths.
    """
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    
    directories = [
        os.path.join(base_dir, 'raw'),
        os.path.join(base_dir, 'processed'),
        os.path.join(base_dir, 'results')
    ]
    
    created = []
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            created.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    return created

def main():
    """Entry point for creating data directories."""
    print("Setting up data directories...")
    created_dirs = create_data_directories()
    if created_dirs:
        print(f"Successfully created {len(created_dirs)} new directories.")
    else:
        print("All directories already exist.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
