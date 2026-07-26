import os
import sys

def setup_directories(project_root: str) -> None:
    """
    Creates the standard project directory structure for PROJ-083.
    
    Args:
        project_root: The absolute or relative path to the project root.
    """
    directories = [
        "data/raw",
        "data/processed",
        "data/models",
        "code",
        "tests",
        "docs/reports",
        "specs",
        "figures"
    ]
    
    for dir_path in directories:
        full_path = os.path.join(project_root, dir_path)
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {full_path}")

if __name__ == "__main__":
    # Default to current directory if no argument provided
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    setup_directories(root)
    print("Project structure initialization complete.")
