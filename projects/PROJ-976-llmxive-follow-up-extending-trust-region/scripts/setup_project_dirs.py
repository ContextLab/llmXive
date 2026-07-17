"""
Script to initialize the project directory structure.
Run this before starting data processing pipelines.
"""
from code.config import ensure_directories

if __name__ == "__main__":
    print("Initializing project directories...")
    ensure_directories()
    print("Directories created successfully.")
