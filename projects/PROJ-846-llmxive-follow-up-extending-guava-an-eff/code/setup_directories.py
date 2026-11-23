import os
import sys
from pathlib import Path

def setup_data_directories():
    """
    Creates the required data directory structure for the llmXive project.
    This includes raw, processed, and artifacts directories under the project's data root.
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the project root based on the task context
    project_root = Path(__file__).resolve().parent.parent.parent
    project_name = "PROJ-846-llmxive-follow-up-extending-guava-an-eff"
    base_data_path = project_root / project_name / "data"
    
    directories = [
        base_data_path / "raw",
        base_data_path / "processed",
        base_data_path / "artifacts"
    ]
    
    created_count = 0
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {directory}")
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")
            return False
    
    print(f"Successfully created {created_count} data directories.")
    return True

def main():
    """Main entry point for directory setup."""
    success = setup_data_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
