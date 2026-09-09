import os
from pathlib import Path


def main():
    """
    Create the required artifacts subdirectories:
    - artifacts/models
    - artifacts/reports
    - artifacts/figures

    Creates .gitkeep files in each directory to ensure they are tracked by git.
    """
    # Determine the project root based on the script location
    # The script is located at code/create_artifact_dirs.py
    # Project root is two levels up
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    artifacts_root = project_root / "artifacts"

    # Define the required subdirectories
    subdirs = ["models", "reports", "figures"]

    for subdir_name in subdirs:
        dir_path = artifacts_root / subdir_name
        
        # Create the directory if it doesn't exist
        os.makedirs(dir_path, exist_ok=True)
        
        # Create .gitkeep file
        gitkeep_path = dir_path / ".gitkeep"
        gitkeep_path.touch()
        
        print(f"Created directory: {dir_path}")
        print(f"Created .gitkeep: {gitkeep_path}")

    print("Artifact directory structure created successfully.")


if __name__ == "__main__":
    main()
