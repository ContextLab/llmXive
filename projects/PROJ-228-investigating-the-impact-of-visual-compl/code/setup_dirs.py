import os
from pathlib import Path

def create_data_directories():
    """Create data directory structure."""
    dirs = [
        'data/raw',
        'data/interim',
        'data/results'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def create_test_directories():
    """Create test directory structure."""
    dirs = [
        'tests/unit',
        'tests/integration'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def create_source_directories():
    """Create source directory structure."""
    dirs = [
        'code'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def create_docs_directory():
    """Create docs directory structure."""
    Path('docs').mkdir(parents=True, exist_ok=True)

def create_all_directories():
    """Create all necessary directories."""
    create_data_directories()
    create_test_directories()
    create_source_directories()
    create_docs_directory()

def main():
    """Main entry point."""
    create_all_directories()
    print("All directories created.")

if __name__ == "__main__":
    main()
