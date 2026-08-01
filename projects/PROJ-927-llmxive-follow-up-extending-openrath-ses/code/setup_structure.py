import os
import stat
from pathlib import Path

def create_structure(base_path: str = "projects/PROJ-927-llmxive-follow-up-extending-openrath-ses"):
    """
    Creates the project directory structure and initializes empty __init__.py files
    as required by task T001.
    """
    base = Path(base_path)
    
    # Define directories to create
    directories = [
        "code",
        "code/generators",
        "code/executors",
        "code/simulators",
        "code/reconstructors",
        "code/analyzers",
        "tests",
        "data/raw/workflows",
        "data/processed/event_log",
        "data/processed/session_first",
        "data/processed/results",
        "state"
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = base / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create __init__.py files
    init_dirs = [
        "code",
        "code/generators",
        "code/executors",
        "code/simulators",
        "code/reconstructors",
        "code/analyzers",
        "tests",
        "data/raw/workflows",
        "data/processed/event_log",
        "data/processed/session_first",
        "data/processed/results",
        "state"
    ]
    
    for dir_path in init_dirs:
        full_path = base / dir_path / "__init__.py"
        # Only create if it doesn't exist to avoid overwriting existing content
        if not full_path.exists():
            full_path.touch()
            print(f"Created empty __init__.py: {full_path}")
        else:
            print(f"Skipped existing __init__.py: {full_path}")

    print(f"Project structure created at: {base}")

if __name__ == "__main__":
    create_structure()
