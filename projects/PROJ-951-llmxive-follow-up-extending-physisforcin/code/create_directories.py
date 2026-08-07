import os
from pathlib import Path

def main():
    """
    Creates the root project directory structure for PROJ-951-llmxive-follow-up-extending-physisforcin
    under projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/.
    
    This satisfies T001: Create project root directories.
    """
    # Define the base project path relative to the current working directory
    # The task specifies: projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
    project_root = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin")
    code_dir = project_root / "code"
    
    print(f"Ensuring project root exists: {project_root}")
    project_root.mkdir(parents=True, exist_ok=True)
    
    print(f"Ensuring code directory exists: {code_dir}")
    code_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify creation
    if code_dir.exists() and code_dir.is_dir():
        print(f"Successfully created directory: {code_dir}")
        print("Directory structure created for T001.")
    else:
        raise RuntimeError(f"Failed to create directory: {code_dir}")

if __name__ == "__main__":
    main()