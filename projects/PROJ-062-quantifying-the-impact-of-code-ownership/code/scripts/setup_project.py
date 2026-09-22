"""
Script to create the project directory structure for PROJ-062.
This task implements T001: Create project structure per implementation plan.
"""
import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the required directory structure for the project.
    Based on the implementation plan for PROJ-062.
    """
    # Define the project root relative to the script location or current working directory
    # The task specifically asks for: projects/PROJ-062-quantifying-the-impact-of-code-ownership/
    # However, the project context implies we are ALREADY inside that project directory
    # (based on the prompt: "You are working on project PROJ-062...").
    # Therefore, we will create the standard internal structure required by the pipeline
    # (data, code, tests, specs, state) and ensure the top-level project folder exists if we are running from a parent.

    # Determine base path: If we are in code/scripts/, go up 2 levels to project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent

    # Ensure the specific project directory name exists if we are running from a generic parent
    # But since the prompt says we are working ON this project, we assume project_root IS the project dir.
    # We will create the internal structure.

    # Directories to create
    directories = [
        "code",
        "code/utils",
        "code/scripts",
        "data",
        "data/raw",
        "data/intermediate",
        "data/results",
        "tests",
        "tests/unit",
        "tests/integration",
        "specs",
        "specs/001-code-ownership-analysis",
        "state",
        "figures",
        "docs"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")

    # Create .gitkeep files in data directories as per T004 requirement (often grouped with structure setup)
    # T004 is marked as needing redo, but creating these now ensures T001/T004 are both satisfied.
    gitkeep_dirs = [
        "data/raw",
        "data/intermediate",
        "data/results"
    ]

    for dir_path in gitkeep_dirs:
        full_path = project_root / dir_path
        gitkeep_file = full_path / ".gitkeep"
        if not gitkeep_file.exists():
            gitkeep_file.touch()
            print(f"Created .gitkeep: {gitkeep_file}")
        else:
            print(f".gitkeep exists: {gitkeep_file}")

    # Create __init__.py files in Python packages
    python_dirs = [
        "code",
        "code/utils",
        "code/scripts",
        "tests",
        "tests/unit",
        "tests/integration"
    ]

    for dir_path in python_dirs:
        full_path = project_root / dir_path
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py: {init_file}")
        else:
            print(f"__init__.py exists: {init_file}")

    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for the script."""
    print("Starting project structure creation...")
    try:
        create_structure()
        print("Success.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
