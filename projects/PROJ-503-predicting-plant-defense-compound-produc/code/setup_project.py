import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-503.
    This script ensures all required directories exist as per T001.
    """
    # Define the project root relative to the script location or current working directory
    # Assuming this script is run from the repo root or the project root
    # We construct the path based on the task requirement
    
    # The task requires specific paths under:
    # projects/PROJ-503-predicting-plant-defense-compound-produc/
    
    # We will assume the script is run from the repository root.
    # If run from elsewhere, we adjust based on __file__ or CWD.
    # To be safe and robust, we define the project root explicitly.
    
    script_dir = Path(__file__).resolve().parent
    # The script is inside code/, so project root is parent of code/
    project_root = script_dir.parent 
    
    # However, the task paths are relative to the repo root which might be the parent of 'projects'
    # Let's check if 'projects' exists in parent of project_root
    if project_root.name == "code":
        potential_project_root = project_root.parent
        if potential_project_root.name == "PROJ-503-predicting-plant-defense-compound-produc":
            project_root = potential_project_root
        else:
            # Fallback: assume current working directory is the repo root
            project_root = Path.cwd() / "projects" / "PROJ-503-predicting-plant-defense-compound-produc"
    
    # If the path logic above is complex, let's just ensure the directories exist relative to the project root
    # The task specifies exact paths. We will create them relative to the project root.
    
    # Re-evaluating: The task says "Create project structure with exact directories: projects/PROJ-503.../code/..."
    # This implies the script should create these if they don't exist.
    # We will assume the current working directory is the repository root where 'projects' folder lives.
    # If the script is run as `python code/setup_project.py`, the CWD might be the repo root.
    
    base_path = Path.cwd()
    project_path = base_path / "projects" / "PROJ-503-predicting-plant-defense-compound-produc"
    
    # If we are running from inside the project, adjust
    if not project_path.exists():
        # Try relative to script
        script_path = Path(__file__).resolve()
        # script is code/setup_project.py -> parent is code -> parent is project
        candidate = script_path.parent.parent
        if candidate.name == "PROJ-503-predicting-plant-defense-compound-produc":
            project_path = candidate
        else:
            # Fallback to creating in CWD/projects/...
            project_path = Path.cwd() / "projects" / "PROJ-503-predicting-plant-defense-compound-produc"

    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/paired",
        "logs",
        "outputs/models",
        "docs",
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]

    created_count = 0
    for dir_name in directories:
        full_path = project_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nProject structure setup complete for: {project_path}")
    print(f"Total directories created: {created_count}")
    
    # Verification step: List created structure
    print("\nVerification - Directory Tree:")
    for root, dirs, files in os.walk(project_path):
        level = root.replace(str(project_path), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        # Only print directories to keep output clean, or limit depth
        for d in dirs:
            print(f'{subindent}{d}/')

    return 0

if __name__ == "__main__":
    sys.exit(main())