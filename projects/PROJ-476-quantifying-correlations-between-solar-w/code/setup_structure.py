import os
import sys

def main():
    """
    Create the project directory structure for artifacts and state directories.
    This script ensures the existence of:
    - artifacts/figures
    - artifacts/reports
    - state/
    
    It also ensures the 'artifacts' and 'state' parent directories exist.
    """
    # Define the directories to create relative to the project root
    # We assume this script is run from the project root or code/ directory.
    # To be safe, we determine the project root based on the script location.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    directories = [
        os.path.join(project_root, "artifacts", "figures"),
        os.path.join(project_root, "artifacts", "reports"),
        os.path.join(project_root, "state"),
    ]
    
    created_count = 0
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")

if __name__ == "__main__":
    main()
