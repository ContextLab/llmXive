import os
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-710.
    This script ensures all required directories exist relative to the project root.
    """
    # Determine project root based on the script location (assuming script is in code/)
    # The task specifies paths relative to the project root:
    # projects/PROJ-710-robustness-of-confidence-intervals-to-di/
    
    # Since this script is being run as part of the implementation,
    # we assume the current working directory is the project root.
    # However, to be safe and explicit, we define the base path.
    
    base_dir = Path.cwd()
    project_name = "PROJ-710-robustness-of-confidence-intervals-to-di"
    project_root = base_dir / project_name

    # Define the required subdirectories relative to the project root
    # Note: The task description lists paths like `projects/.../code/`,
    # but standard project structure usually implies the project root IS the repo or a subfolder.
    # Given the constraint "Stay inside the project tree" and "All artifact paths are relative to the project root",
    # and the existing completed tasks (T001b, T001c, etc.) imply files like `code/config.py` exist at the root level of the project context.
    # The task description's path `projects/PROJ-710-.../code/` suggests a nested structure.
    # However, the "Existing project API surface" shows imports like `from analysis.ci_builder` which implies the `code/` folder is on the PYTHONPATH or the root.
    # Let's strictly follow the task description's path requirement:
    # `projects/PROJ-710-robustness-of-confidence-intervals-to-di/code/`
    
    # If the current directory is the repo root, we create the `projects/` folder.
    # If the current directory is already the project root, we create the subfolders.
    # Given the ambiguity, we will create the full path structure as requested in the task description
    # relative to the current working directory.
    
    dirs_to_create = [
        "code",
        "code/data",
        "code/analysis",
        "code/utils",
        "code/tests",
        "artifacts"
    ]

    # Check if we are inside the project folder or if we need to create the project folder
    # The task says: "Create project directory structure: projects/PROJ-710-.../code/..."
    # This implies the script might be run from the repo root.
    
    target_root = project_root
    
    # Ensure the target root exists
    target_root.mkdir(parents=True, exist_ok=True)

    for dir_path in dirs_to_create:
        full_path = target_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Create __init__.py files to ensure they are recognized as packages
    # (Though T001b is marked complete, this script ensures the structure is valid)
    init_files = []
    for dir_path in dirs_to_create:
        full_path = target_root / dir_path
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            init_files.append(init_file)
            print(f"Created __init__.py: {init_file}")
        else:
            # If it exists, we assume T001b handled it, but we can touch it to ensure freshness
            pass

    print(f"Project structure for {project_name} created successfully.")

if __name__ == "__main__":
    main()