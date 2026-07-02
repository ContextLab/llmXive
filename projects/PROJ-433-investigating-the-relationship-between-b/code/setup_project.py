"""
Script to initialize the project directory structure for llmXive research pipeline.
Creates necessary directories for data, code, tests, and state management.
"""
import os
import sys

def main():
    """Create the standard project directory structure."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define directories relative to project root
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests",
        "state"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(root_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure initialization complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())