import os
from pathlib import Path

def create_directories() -> None:
    """
    Create the project directory structure as defined in the implementation plan.
    
    Creates the following directories relative to the project root:
    - code/
    - code/utils/
    - tests/
    - data/raw/
    - data/processed/
    - data/results/
    - data/results/diagnostics/
    - logs/
    - contracts/
    - figures/
    """
    # Define the base project root (assuming this script is run from project root or code/)
    # We will assume the script is run from the project root.
    base_path = Path.cwd()
    
    directories = [
        "code",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "data/results/diagnostics",
        "logs",
        "contracts",
        "figures",
        "specs"
    ]
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
