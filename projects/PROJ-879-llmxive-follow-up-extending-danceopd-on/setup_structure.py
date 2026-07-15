"""
Script to initialize the project directory structure for llmXive follow-up.
Creates all necessary directories as defined in the implementation plan.
"""
import os
import sys
from pathlib import Path

def create_directories():
    # Define the base project path relative to the current working directory
    # Assuming this script runs from the project root or a parent directory
    base_path = Path("projects/PROJ-879-llmxive-follow-up-extending-danceopd-on")
    
    # Define all required directories relative to the base path
    directories = [
        # Code structure
        "code",
        "code/utils",
        "code/data",
        "code/models",
        "code/metrics",
        
        # Data structure
        "data/raw",
        "data/processed",
        "data/results",
        
        # Models storage
        "models",
        
        # Tests structure
        "tests/unit",
        "tests/integration",
        
        # Specs structure
        "specs/contracts",
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Initializing project structure at: {base_path.absolute()}")
    
    for dir_name in directories:
        full_path = base_path / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.exists() and full_path.is_dir():
                # Check if it was just created or already existed
                # Since exist_ok=True, we can't easily distinguish without tracking state,
                # but for the purpose of this script, we just ensure it exists.
                created_count += 1
                print(f"  ✓ Created/Verified: {full_path}")
            else:
                print(f"  ✗ Failed to create: {full_path}")
        except Exception as e:
            print(f"  ✗ Error creating {full_path}: {e}")
            return 1
    
    print(f"\nProject structure initialized successfully.")
    print(f"Directories processed: {len(directories)}")
    return 0

if __name__ == "__main__":
    sys.exit(create_directories())