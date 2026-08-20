import os
import sys
from pathlib import Path

def main():
    """
    Creates the physical directory structure for the project.
    Executes the equivalent of:
    mkdir -p code tests data/raw data/generated data/results state/projects
    """
    # Define the project root based on the task description
    # The task implies we are working within projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/
    # However, to be safe and portable, we create the structure relative to the current working directory
    # or the script's location if run as an entry point.
    # The task specifically asks to establish the layout under the project root.
    
    # We will create the directories relative to the current working directory (CWD)
    # as this is standard for CLI tools run from the project root.
    
    project_root = Path.cwd()
    
    # Define the required directories
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/generated",
        "data/results",
        "state/projects"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
            else:
                print(f"Directory already exists: {full_path}")
                existing_count += 1
        except PermissionError:
            print(f"Error: Permission denied creating {full_path}")
            return 1
        except OSError as e:
            print(f"Error creating {full_path}: {e}")
            return 1
    
    print(f"Setup complete. Created {created_count} directories, {existing_count} already existed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
