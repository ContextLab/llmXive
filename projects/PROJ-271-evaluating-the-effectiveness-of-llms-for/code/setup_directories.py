import os
from pathlib import Path

def create_project_directories():
    """
    Creates the required directory structure for the project.
    
    This function creates the following directories relative to the project root:
    - projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/code/
    - projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/data/raw/
    - projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/data/processed/
    - projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/results/
    - projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/tests/unit/
    - projects/PROJ-271-evaluating-the-effectiveness-of-llms-for/tests/contract/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    project_root = Path("projects/PROJ-271-evaluating-the-effectiveness-of-llms-for")
    
    directories = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "tests" / "unit",
        project_root / "tests" / "contract",
    ]
    
    created_count = 0
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
        except OSError as e:
            print(f"Error creating directory {directory}: {e}")
    
    print(f"Successfully created {created_count}/{len(directories)} directories.")
    return created_count == len(directories)

if __name__ == "__main__":
    success = create_project_directories()
    if success:
        print("Directory setup completed successfully.")
    else:
        print("Directory setup encountered errors.")
        exit(1)
