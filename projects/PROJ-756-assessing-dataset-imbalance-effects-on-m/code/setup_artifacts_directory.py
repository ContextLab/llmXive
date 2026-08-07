import os
import sys
from pathlib import Path

def create_artifacts_directory(base_path: Path) -> None:
    """
    Creates the 'artifacts' directory under the project root if it doesn't exist.
    
    Args:
        base_path: The root path of the project (e.g., projects/PROJ-756-...)
    """
    artifacts_dir = base_path / "artifacts"
    if not artifacts_dir.exists():
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {artifacts_dir}")
    else:
        print(f"Directory already exists: {artifacts_dir}")

def main() -> None:
    """
    Entry point to create the artifacts directory.
    Assumes the script is run from the project root or passed the project root.
    """
    # Determine project root based on the expected structure relative to this script
    # This script lives in code/, so project root is parent of code/
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent 
    
    if not project_root.name.startswith("PROJ-"):
        print(f"Warning: Current project root '{project_root}' does not match expected PROJ-756 pattern. Proceeding anyway.")
    
    create_artifacts_directory(project_root)

if __name__ == "__main__":
    main()
