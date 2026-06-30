import os
from pathlib import Path

def setup_directories():
    """
    Create the necessary directory structure for the research project.
    
    This function ensures that the 'code' and 'tests' directories exist
    at the project root level.
    
    Returns:
        dict: A dictionary containing the paths of created/existing directories.
    """
    # Define the project root relative to this script's location
    # Assuming this script is run from the project root or the script location is the project root
    # The task specifies paths relative to the project root.
    project_root = Path(__file__).resolve().parent.parent
    
    directories = {
        'code': project_root / 'code',
        'tests': project_root / 'tests'
    }
    
    created = []
    for name, path in directories.items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
            print(f"Created directory: {path}")
        else:
            print(f"Directory already exists: {path}")
    
    return {
        "status": "success",
        "directories": directories,
        "created": created
    }

if __name__ == "__main__":
    result = setup_directories()
    print(f"Setup complete: {result}")