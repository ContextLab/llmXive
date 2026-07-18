import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-057-investigating-the-impact-of-compiler-opt
    as defined in tasks.md T001.
    
    Structure:
    code/{kernels,benchmarks,analysis,utils}
    data/{raw,intermediates,results}
    tests/{unit,integration}
    """
    project_root = Path(__file__).resolve().parent.parent
    project_name = "PROJ-057-investigating-the-impact-of-compiler-opt"
    
    # Define the base path for the project structure
    # The task implies creating this inside a 'projects' folder or relative to root
    # Based on standard conventions and the task description "projects/PROJ-057..."
    base_path = project_root / "projects" / project_name
    
    directories = [
        "code/kernels",
        "code/benchmarks",
        "code/analysis",
        "code/utils",
        "data/raw",
        "data/intermediates",
        "data/results",
        "tests/unit",
        "tests/integration"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
        created_count += 1
    
    print(f"Successfully created {created_count} directories for project {project_name}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())