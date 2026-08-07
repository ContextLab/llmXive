"""
Task T001: Create project root directories under projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/.

This script creates the root directory structure for the project.
It ensures the base path exists and prepares for subdirectory creation (T001b).
"""
import os
import sys
from pathlib import Path

def main():
    """Main entry point for T001 directory creation."""
    # Define the project root path relative to the current working directory
    # The task specifies: projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
    project_root = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code")
    
    print(f"Creating project root directory: {project_root.absolute()}")
    
    try:
        # Create the directory and all parent directories if they don't exist
        project_root.mkdir(parents=True, exist_ok=True)
        
        if project_root.exists() and project_root.is_dir():
            print(f"SUCCESS: Root directory created at {project_root.absolute()}")
            print(f"Directory contents: {list(project_root.iterdir())}")
            return 0
        else:
            print(f"ERROR: Failed to create directory {project_root}")
            return 1
            
    except PermissionError as e:
        print(f"ERROR: Permission denied creating directory {project_root}: {e}")
        return 1
    except OSError as e:
        print(f"ERROR: OS error creating directory {project_root}: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
