import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-181.
    Creates the root project folder and all required subdirectories.
    """
    # Define the project root relative to the script location or current working directory
    # The task specifies the project is at projects/PROJ-181-predicting-species-distribution-shifts-u/
    # We assume the script is run from the repository root or the parent of 'projects'
    project_root = Path.cwd() / "projects" / "PROJ-181-predicting-species-distribution-shifts-u"
    
    # Define all required directories
    directories = [
        "code",
        "data",
        "tests",
        "metrics",
        "reports",
        "logs",
        "state",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests/unit",
        "tests/integration",
        "contracts"
    ]

    print(f"Initializing project structure at: {project_root}")
    
    created_count = 0
    for dir_name in directories:
        full_path = project_root / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create __init__.py files to ensure they are treated as Python packages
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "code" / "utils" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "tests" / "unit" / "__init__.py",
        project_root / "tests" / "integration" / "__init__.py",
    ]
    
    # Ensure utils directory exists before creating __init__.py there
    (project_root / "code" / "utils").mkdir(parents=True, exist_ok=True)

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created init file: {init_file}")
        
    print(f"Project initialization complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())