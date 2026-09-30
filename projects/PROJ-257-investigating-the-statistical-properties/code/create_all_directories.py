import os
from pathlib import Path

def create_directories():
    """Create the full project directory structure as specified in T001."""
    base = Path(".")
    
    # Define the directory structure
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "output/results",
        "output/figures",
        "logs",
        "src/data",
        "src/analysis",
        "src/viz",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    for dir_path in directories:
        full_path = base / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path}")

def main():
    create_directories()

if __name__ == "__main__":
    main()
