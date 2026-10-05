"""
Setup script to create the root project directory structure for llmXive.
Implements T001: Create root project directories and test directories.
"""
import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the required directory structure for the llmXive project.
    Verifies creation and prints the tree structure.
    """
    # Project root is the parent of this file's directory (code/)
    # But tasks.md says "Create root project directories (projects/PROJ-...)"
    # We assume the script runs from the project root or we derive it.
    # The task specifies: projects/PROJ-915-llmxive-follow-up-extending-measuring-ep/
    
    # Determine the base path: we assume the current working directory is the repo root
    # or the script is run from the repo root.
    base_path = Path.cwd()
    
    # The specific project directory as per T001
    project_dir_name = "PROJ-915-llmxive-follow-up-extending-measuring-ep"
    # The task says "Create root project directories (projects/PROJ-...)"
    # implying a 'projects' folder at the root.
    projects_root = base_path / "projects"
    project_root = projects_root / project_dir_name

    # Ensure the projects root exists
    projects_root.mkdir(parents=True, exist_ok=True)

    # Define all required directories relative to the project root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "data/results",
        "state",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_paths = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(full_path)

    # Verification: Print the tree structure
    print(f"Created project structure at: {project_root}")
    print("Directory structure:")
    for path in sorted(created_paths):
        rel_path = path.relative_to(project_root)
        print(f"  {rel_path}")
    
    # Verify existence
    missing = []
    for path in created_paths:
        if not path.exists():
            missing.append(str(path))
    
    if missing:
        print(f"ERROR: The following directories were not created: {missing}")
        sys.exit(1)
    
    print("Verification: All directories created successfully.")
    return True

def main():
    setup_directories()

if __name__ == "__main__":
    main()
