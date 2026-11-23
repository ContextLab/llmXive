"""
Script to initialize the project directory structure for T001b.
Creates the code/ directory and its subdirectories: data/, inference/, analysis/, utils/.
"""
import os
from pathlib import Path

def create_directory_structure(root_path: Path) -> None:
    """
    Creates the required directory structure under the root path.
    
    Args:
        root_path: The base directory where 'code/' will be created.
    """
    code_dir = root_path / "code"
    sub_dirs = ["data", "inference", "analysis", "utils"]

    # Create the main code directory
    code_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {code_dir}")

    # Create subdirectories
    for subdir in sub_dirs:
        dir_path = code_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    # Create .gitkeep files to ensure directories are tracked by git
    for subdir in sub_dirs:
        gitkeep_path = code_dir / subdir / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep: {gitkeep_path}")

def main():
    """
    Main entry point. Assumes the script is run from the project root
    or calculates the root based on the project name.
    """
    # Determine the project root. 
    # Since this script is in code/, we go up one level to the project root.
    # However, for T001a/T001b, the root is defined as:
    # projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2/
    
    # We assume the script is executed from the project root directory
    # or we explicitly construct the path if we know the project name.
    # To be safe and portable, we look for the parent of the script location
    # and assume that is the project root (where 'code' should be created).
    
    script_path = Path(__file__).resolve()
    current_dir = script_path.parent
    
    # If the script is inside 'code/', the project root is the parent of 'code'
    if current_dir.name == "code":
        project_root = current_dir.parent
    else:
        # Fallback: assume current working directory is the project root
        project_root = Path.cwd()

    print(f"Project root detected/used: {project_root}")
    create_directory_structure(project_root)
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()