import os
from pathlib import Path

def create_project_structure():
    """
    Creates the required project directory structure for artifacts and state.
    This implements the logic for T001 and T001b.
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    # Directories for code (T001)
    code_dirs = [
        base_dir / "code" / "data",
        base_dir / "code" / "analysis",
        base_dir / "code" / "viz",
        base_dir / "code" / "tests",
    ]
    
    # Directories for artifacts and state (T001b)
    # artifacts/figures, artifacts/reports, state/
    artifact_dirs = [
        base_dir / "artifacts" / "figures",
        base_dir / "artifacts" / "reports",
        base_dir / "state",
    ]
    
    all_dirs = code_dirs + artifact_dirs
    
    for dir_path in all_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

if __name__ == "__main__":
    create_project_structure()