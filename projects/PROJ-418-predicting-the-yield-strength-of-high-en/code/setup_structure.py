import os
import sys

def create_directories():
    """
    Create the required directory structure for the HEA Yield Strength project.
    Creates: code/, data/raw, data/processed, output/, output/plots, tests/
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    directories = [
        os.path.join(base_dir, "code"),
        os.path.join(base_dir, "data", "raw"),
        os.path.join(base_dir, "data", "processed"),
        os.path.join(base_dir, "output"),
        os.path.join(base_dir, "output", "plots"),
        os.path.join(base_dir, "tests"),
    ]
    
    created_count = 0
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return created_count

if __name__ == "__main__":
    create_directories()
