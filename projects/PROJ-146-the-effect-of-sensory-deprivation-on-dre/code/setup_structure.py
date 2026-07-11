import os
import sys

def create_structure():
    """
    Creates the project directory structure for PROJ-146.
    This function ensures all required directories exist as per the implementation plan.
    """
    base_path = "projects/PROJ-146-the-effect-of-sensory-deprivation-on-dre"
    
    # Define all required subdirectories relative to the base path
    directories = [
        "data/raw",
        "data/synthetic",
        "data/processed",
        "data/protocols",
        "data/ethics",
        "code",
        "results/models",
        "results/reports",
        "tests/unit",
        "tests/contract",
        "tests/integration"
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = os.path.join(base_path, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created_dirs.append(full_path)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    if not created_dirs:
        print("All required directories already exist.")
    else:
        print(f"\nSuccessfully created {len(created_dirs)} directory structure(s).")
    
    return created_dirs

if __name__ == "__main__":
    create_structure()