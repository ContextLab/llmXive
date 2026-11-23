import os
import sys
from pathlib import Path

def ensure_directories():
    """
    Create the project directory structure for PROJ-268.
    Verifies existence using os.path.isdir.
    """
    # Define the project root relative to the code directory
    # The project structure is: projects/PROJ-268-.../
    # Since this script lives in code/, we go up one level to find 'projects'
    # However, tasks.md says paths are relative to project root.
    # We assume the script is run from the project root or code/ subdirectory.
    # To be safe, we calculate relative to the script's location if needed,
    # but standard practice in these pipelines is to run from root.
    
    # Let's assume the current working directory is the project root.
    # If not, we try to locate 'projects' relative to this script.
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    project_name = "PROJ-268-the-impact-of-network-centrality-on-neur"
    base_path = project_root / "projects" / project_name

    required_dirs = [
        base_path,
        base_path / "code",
        base_path / "data",
        base_path / "tests",
        base_path / "state"
    ]

    created_count = 0
    verified_count = 0

    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            verified_count += 1
            print(f"Directory already exists: {dir_path}")

        # Verify using os.path.isdir as requested
        if not os.path.isdir(str(dir_path)):
            raise RuntimeError(f"Failed to verify directory creation: {dir_path}")

    print(f"Directory setup complete. Created: {created_count}, Verified: {verified_count}")
    return True

def main():
    """Entry point for project setup."""
    try:
        ensure_directories()
        print("Project structure verification successful.")
        return 0
    except Exception as e:
        print(f"Error during project setup: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())