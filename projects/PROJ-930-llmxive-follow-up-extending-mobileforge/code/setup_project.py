import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure and initial files as per T001.
    """
    project_root = Path(__file__).resolve().parent
    base_path = project_root / "projects" / "PROJ-930-llmxive-follow-up-extending-mobileforge"
    
    # Ensure base path exists
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Define directories to create
    dirs = [
        "code/data/raw",
        "code/data/processed",
        "code/data/evaluation",
        "code/models",
        "code/utils",
        "code/tests/unit",
        "code/tests/integration"
    ]
    
    for d in dirs:
        dir_path = base_path / d
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Define files to create (touch)
    files = [
        "code/requirements.txt",
        "code/README.md"
    ]
    
    for f in files:
        file_path = base_path / f
        if not file_path.exists():
            file_path.touch()
            print(f"Created file: {file_path}")
        else:
            print(f"File already exists: {file_path}")
    
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
