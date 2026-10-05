import os
from pathlib import Path

def main():
    """
    Execute Source Directory Creation for the llmXive project.
    Creates the necessary directory structure for generators, inference, and analysis modules.
    """
    project_root = Path(____).parent.resolve()
    
    # Define the directories to be created relative to the project root
    directories = [
        "src/generators",
        "src/inference",
        "src/analysis"
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

if __name__ == "__main__":
    main()
