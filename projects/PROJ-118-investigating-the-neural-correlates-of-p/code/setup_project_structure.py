import os
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-118.
    Directories created relative to the project root:
    - data/raw
    - data/processed
    - code
    - tests
    - results
    """
    # Define the project root. 
    # We assume the script is run from the project root or that we create 
    # the structure relative to the current working directory.
    # Per the task: "projects/PROJ-118-investigating-the-neural-correlates-of-p/"
    # We will create the structure in the current working directory as the root
    # of the project implementation, or explicitly create the subdirectory if 
    # we are running from a parent.
    # Given the constraints "Stay inside the project tree", we assume the 
    # working directory is the project root or we create the specific path.
    
    project_name = "PROJ-118-investigating-the-neural-correlates-of-p"
    base_path = Path(project_name)
    
    # Create the base project directory if it doesn't exist
    base_path.mkdir(exist_ok=True)
    
    # Define required directories
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results"
    ]
    
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
        
    print(f"Project structure for {project_name} created successfully.")

if __name__ == "__main__":
    main()
