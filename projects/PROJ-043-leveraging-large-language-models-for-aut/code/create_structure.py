import os
import sys

def create_structure(base_path: str) -> None:
    """
    Create the full nested directory tree for the project.
    
    Creates:
    - code/, code/data/, code/llm/, code/models/, code/utils/
    - data/, data/raw/, data/processed/, data/cache/, data/results/
    - tests/
    - paper/
    - contracts/
    
    Args:
        base_path: The root directory where the project structure will be created.
    """
    # Define all required directories relative to base_path
    directories = [
        "code",
        "code/data",
        "code/llm",
        "code/models",
        "code/utils",
        "data",
        "data/raw",
        "data/processed",
        "data/cache",
        "data/results",
        "tests",
        "paper",
        "contracts",
    ]

    for dir_path in directories:
        full_path = os.path.join(base_path, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_structure.py <project_root_path>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    create_structure(project_root)
    print(f"Project structure created successfully at: {project_root}")