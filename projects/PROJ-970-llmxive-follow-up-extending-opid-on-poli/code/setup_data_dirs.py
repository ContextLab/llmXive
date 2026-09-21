"""
Script to create the required directory structure for the llmXive project.
This ensures all necessary folders exist before running experiments.
"""
import os
import sys
from typing import List

# Define the root project directory (assumed to be the parent of this script's location if run as module, or current dir)
# However, based on the API surface, this script is at code/setup_data_dirs.py
# We need to create directories relative to the project root.
# The project root is typically the parent of 'code'.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIRECTORIES = [
    "src",
    "src/environment",
    "src/agent",
    "src/simulation",
    "src/analysis",
    "tests",
    "data/raw/synthetic_graphs",
    "data/processed",
    # Additional directories implied by the API surface to ensure imports work if they don't exist yet
    "data",
    "data/raw",
    "src/utils",
    "src/env", # Mapped to env.state_graph in imports
    "src/experiments",
    "src/simulation", # Already listed
    "src/analysis",   # Already listed
]

def create_directories() -> List[str]:
    """
    Creates all required directories relative to the project root.
    Returns a list of created directory paths.
    """
    created = []
    for dir_path in DIRECTORIES:
        full_path = os.path.join(PROJECT_ROOT, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            created.append(full_path)
            print(f"Created directory: {full_path}")
        else:
            # Ensure it's actually a directory, not a file
            if not os.path.isdir(full_path):
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    return created

def main():
    """Main entry point for directory creation."""
    print(f"Project Root: {PROJECT_ROOT}")
    print("Creating directory structure...")
    created = create_directories()
    if created:
        print(f"Successfully created {len(created)} directories.")
    else:
        print("All directories already exist.")
    
    # Verify structure by printing a summary
    print("\nDirectory Structure Verification:")
    for dir_path in DIRECTORIES:
        full_path = os.path.join(PROJECT_ROOT, dir_path)
        exists = "YES" if os.path.isdir(full_path) else "NO"
        print(f"  [{exists}] {dir_path}")

if __name__ == "__main__":
    main()