import os
from pathlib import Path

def create_project_structure():
    """
    Creates the directory structure and placeholder files for the project.
    This function implements tasks T001a, T001b, T001c, and T001d.
    """
    # Define base paths relative to the script location (project root assumed)
    # We assume this script is run from the project root or code/ directory.
    # To be safe, we resolve relative to the current working directory.
    root = Path.cwd()

    # T001a: Create project directory
    project_dir = root / "projects" / "PROJ-188-evaluating-the-impact-of-llm-generated-c"
    project_dir.mkdir(parents=True, exist_ok=True)

    # T001b: Create code/ and tests/ subdirectories
    code_dir = root / "code"
    tests_dir = root / "tests"
    code_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    # T001c: Create data/ subdirectories
    data_dir = root / "data"
    raw_dir = data_dir / "raw"
    intermediate_dir = data_dir / "intermediate"
    processed_dir = data_dir / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # T001d: Create empty __init__.py files
    (code_dir / "__init__.py").touch()
    (tests_dir / "__init__.py").touch()

    # Create project-specific __init__.py if needed, though not explicitly requested for T001a-d
    # (project_dir / "__init__.py").touch()

    print(f"Project structure created at: {project_dir}")
    print(f"Directories created: code/, tests/, data/raw/, data/intermediate/, data/processed/")
    print("Placeholder __init__.py files created.")

if __name__ == "__main__":
    create_project_structure()
