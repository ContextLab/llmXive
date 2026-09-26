import os
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-227.
    This script ensures all required directories exist relative to the project root.
    """
    # Define the project root relative to this script's location (assuming code/ is a subdir)
    # The task requires paths relative to the project root.
    # We assume the script is run from the project root or we calculate root based on execution context.
    # To be safe and robust, we resolve the project root as the parent of the 'code' directory.
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define required directories based on task T001 description
    # Note: The task description lists:
    # `projects/PROJ-227-assessing-the-trade-offs-between-static-/data/raw/`
    # `data/processed/`, `state/`, `code/`, `tests/`
    #
    # Given the project name is PROJ-227... and we are likely inside that project root,
    # we will create the standard subdirectories: data/raw, data/processed, state, code, tests.
    # If the task implies a nested `projects/PROJ-227...` structure, we assume the current
    # working directory IS that project root for the purpose of artifact creation.
    #
    # We will create:
    # 1. data/raw
    # 2. data/processed
    # 3. state
    # 4. code (already exists as we are in code/, but we ensure it exists)
    # 5. tests
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "state",
        "code",
        "tests"
    ]

    created_count = 0
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    # Additionally, if the task strictly requires the nested path structure 
    # `projects/PROJ-227-assessing-the-trade-offs-between-static-/...` 
    # relative to a broader repo root, we check if we need to create that wrapper.
    # However, standard practice for this agent is to assume the current context IS the project.
    # We will also create the specific nested path just in case the "project root" is actually
    # a repo root containing a `projects/` folder.
    
    project_name = "PROJ-227-assessing-the-trade-offs-between-static-"
    nested_path = project_root / "projects" / project_name
    
    # We create the nested structure if it doesn't exist, mapping the inner requirements
    # to the nested location as well to satisfy the literal string in the task.
    # The task says: Create `projects/PROJ-227.../data/raw/`, `data/processed/`, etc.
    # This is slightly ambiguous: does it mean create BOTH sets, or is the first one the full path?
    # We will ensure the nested path `projects/PROJ-227...` contains the required subdirs.
    
    nested_dirs = [
        "data/raw",
        "data/processed",
        "state",
        "code",
        "tests"
    ]
    
    for dir_path in nested_dirs:
        full_path = nested_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created nested directory: {full_path}")
        else:
            print(f"Nested directory already exists: {full_path}")

    print(f"Project structure setup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()
