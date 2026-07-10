import os
import sys

def main():
    """
    Creates the required project directory structure for llmXive.
    Directories created: code/, data/, results/, tests/, contracts/
    """
    # Determine the project root (parent of the 'code' directory where this script lives)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    directories = [
        'code',
        'data',
        'results',
        'tests',
        'contracts'
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = os.path.join(project_root, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    if created_count > 0:
        print(f"Successfully created {created_count} new directories.")
    else:
        print("All directories already exist.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
