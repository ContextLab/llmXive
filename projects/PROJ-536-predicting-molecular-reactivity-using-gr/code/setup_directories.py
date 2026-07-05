import os
import sys

def create_directories(root_dir=None):
    """
    Creates the required directory structure for the project.
    
    Args:
        root_dir (str, optional): The root directory for the project.
            If None, uses the current working directory.
    
    Returns:
        list: A list of created directory paths.
    """
    if root_dir is None:
        root_dir = os.getcwd()
    
    # Define relative directories to create
    relative_dirs = [
        "data",
        "results",
        "models",
        "contracts",
        # Subdirectories for better organization
        "data/raw",
        "data/processed",
        "results/plots",
        "results/logs",
        "models/checkpoints",
        "contracts/schemas"
    ]
    
    created_dirs = []
    
    for rel_path in relative_dirs:
        full_path = os.path.join(root_dir, rel_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created_dirs.append(full_path)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    return created_dirs

if __name__ == "__main__":
    # Default to current directory if no argument provided
    root = sys.argv[1] if len(sys.argv) > 1 else None
    create_directories(root)
