import os
import sys
from pathlib import Path

def setup_project_structure(base_path: Path) -> None:
    """
    Creates the exact directory tree required for the project.
    
    Required directories:
    - src/ (source code)
    - tests/ (unit and integration tests)
    - data/raw/ (raw downloaded data)
    - data/cleaned/ (processed data)
    - data/results/ (analysis outputs)
    - figures/ (plots and visualizations)
    - contracts/ (schema definitions)
    """
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/cleaned",
        "data/results",
        "figures",
        "contracts"
    ]
    
    created_count = 0
    for dir_name in directories:
        target_dir = base_path / dir_name
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            created_count += 1
        else:
            # Ensure it is actually a directory if it exists
            if not target_dir.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {target_dir}")
    
    print(f"Project structure verified/created at {base_path}")
    print(f"Directories created: {created_count}")

def main() -> int:
    """Entry point for script execution."""
    # Determine project root (assuming script is at code/setup_project.py)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    try:
        setup_project_structure(project_root)
        return 0
    except Exception as e:
        print(f"Error setting up project structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
