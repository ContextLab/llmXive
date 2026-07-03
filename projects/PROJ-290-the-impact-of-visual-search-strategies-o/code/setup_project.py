import os
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-290.
    Implements Task T001a: Create project directories per implementation plan.
    """
    # Define the project root based on the task description
    # The task specifies: projects/PROJ-290-the-impact-of-visual-search-strategies-o/
    # Since we are running this script from the repository root, we assume the script
    # is located at the root or we create the structure relative to the current working directory.
    
    # However, looking at the "Existing project API surface", files like `code/config.py`
    # are already referenced as existing. The task asks to create directories under
    # `projects/PROJ-290-the-impact-of-visual-search-strategies-o/`.
    # To ensure the script works regardless of where it's run from (as long as it's in the repo root),
    # we will create the structure relative to the current working directory.
    
    project_root = Path.cwd()
    
    # The specific project folder name as requested
    project_name = "PROJ-290-the-impact-of-visual-search-strategies-o"
    project_path = project_root / project_name
    
    # Define the required subdirectories
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "results/figures",
        "results/reports",
        "tests",
        "state"
    ]
    
    print(f"Creating project structure in: {project_path}")
    
    created_count = 0
    for dir_name in required_dirs:
        full_path = project_path / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {full_path}")
            created_count += 1
        except Exception as e:
            print(f"  Error creating {full_path}: {e}")
    
    print(f"Project setup complete. {created_count} directories created.")
    
    # Return 0 for success, 1 for failure if any critical dir missing
    return 0 if created_count == len(required_dirs) else 1

if __name__ == "__main__":
    exit(main())