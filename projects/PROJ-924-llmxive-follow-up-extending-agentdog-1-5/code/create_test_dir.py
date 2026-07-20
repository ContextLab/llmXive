"""
Task T001e: Create directory `projects/PROJ-924-llmxive-follow-up-extending-agentdog-1-5/data/test/`

This script ensures the existence of the test data directory as required by the project setup.
It uses the project's root path logic to construct the correct relative path.
"""
import os
from pathlib import Path

def ensure_test_directory():
    """Creates the data/test directory if it does not exist."""
    # Determine the project root. Assuming this script is run from the project root
    # or we need to resolve relative to the current working directory.
    # The task specifies the path relative to the project root.
    project_root = Path.cwd()
    
    # Construct the target directory path
    target_dir = project_root / "projects" / "PROJ-924-llmxive-follow-up-extending-agentdog-1-5" / "data" / "test"
    
    # Create the directory and any necessary parent directories
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify creation
    if target_dir.exists() and target_dir.is_dir():
        print(f"Successfully created directory: {target_dir}")
        return True
    else:
        raise RuntimeError(f"Failed to create directory: {target_dir}")

def main():
    """Entry point for the script."""
    try:
        ensure_test_directory()
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()