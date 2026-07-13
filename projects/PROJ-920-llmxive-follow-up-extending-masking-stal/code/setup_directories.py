import os
from pathlib import Path

def main():
    """
    Creates the necessary directory structure for the llmXive follow-up project.
    This function ensures that all required directories exist before other tasks begin.
    """
    # Define the project root based on the task description
    # The tasks specify paths relative to: projects/PROJ-920-llmxive-follow-up-extending-masking-stal/
    # However, since this script runs from the project root (as implied by T001-T004 existing),
    # we assume the current working directory is the project root.
    
    project_root = Path.cwd()
    
    # Directories to create (based on T001-T006)
    directories = [
        "data/raw",
        "data/processed",
        "output/plots",
        "code",
        "code/utils",       # T005
        "tests/unit",       # T006
        "tests/integration",# T006
        "tests/contract"    # T006
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

if __name__ == "__main__":
    main()