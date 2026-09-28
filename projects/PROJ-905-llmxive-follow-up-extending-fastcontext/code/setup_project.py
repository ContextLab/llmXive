import os
from pathlib import Path

def main():
    """Create the project directory structure for PROJ-905."""
    base_path = Path("projects/PROJ-905-llmxive-follow-up-extending-fastcontext")
    
    # Define the required directories relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests/unit",
        "tests/integration",
        "specs/contracts",
        "state"
    ]
    
    # Create the base project directory
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Create each subdirectory
    created_dirs = []
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))
    
    print(f"Project structure created at: {base_path}")
    for d in created_dirs:
        print(f"  - {d}")

if __name__ == "__main__":
    main()