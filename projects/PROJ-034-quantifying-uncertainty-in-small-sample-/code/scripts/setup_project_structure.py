"""
Script to create the project directory structure for the llmXive project.
This task (T001) creates the required folder tree as per the implementation plan.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the required directory structure."""
    # Define the root directory (current working directory or specified path)
    root = Path.cwd()
    
    # Define all required directories relative to root
    directories = [
        # Code modules
        "code/simulation",
        "code/models",
        "code/metrics",
        "code/validation",
        "code/plots",
        "code/scripts",
        
        # Data directories
        "data/raw",
        "data/simulated",
        "data/results",
        
        # Test directories
        "tests/unit",
        "tests/integration",
        
        # Documentation
        "docs/paper"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create .gitkeep files in data directories to ensure they are tracked by git
    gitkeep_dirs = ["data/raw", "data/simulated", "data/results"]
    for dir_path in gitkeep_dirs:
        full_path = root / dir_path / ".gitkeep"
        if not full_path.exists():
            full_path.touch()
            print(f"Created .gitkeep: {full_path}")
            created_count += 1
    
    print(f"\nProject structure setup complete. Created {created_count} new items.")
    return True

def main():
    """Entry point for the script."""
    try:
        success = create_directories()
        if success:
            print("Success: Project structure created successfully.")
            sys.exit(0)
        else:
            print("Error: Failed to create project structure.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: An exception occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
