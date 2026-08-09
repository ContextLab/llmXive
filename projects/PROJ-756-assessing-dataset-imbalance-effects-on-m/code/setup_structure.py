import os
import sys
from pathlib import Path

def create_directories():
    """Create the main project directory structure."""
    dirs = [
        'data', 'data/raw', 'data/processed', 'data/synthetic',
        'code', 'tests', 'artifacts', 'results', 'state',
        'logs', 'logs/archive'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    
    # Ensure __init__.py files
    for d in ['code', 'tests', 'data', 'artifacts', 'results', 'state', 'logs', 'logs/archive']:
        (Path(d) / '__init__.py').touch(exist_ok=True)
    
    # Ensure .gitkeep in data subdirs
    for d in ['data/raw', 'data/processed', 'data/synthetic']:
        (Path(d) / '.gitkeep').touch(exist_ok=True)

    print("Directory structure created successfully.")

def main():
    create_directories()

if __name__ == "__main__":
    main()
