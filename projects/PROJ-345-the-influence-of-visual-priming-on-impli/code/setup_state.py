"""
Setup utilities for the project state directory structure.
Implements T002b: Create state/projects/PROJ-345/ directory structure.
"""
import os
from pathlib import Path


def create_state_directories(project_root: Path) -> None:
    """
    Create the directory structure for project state management.
    
    Creates:
    - state/
    - state/projects/
    - state/projects/PROJ-345/
    - state/projects/PROJ-345/logs/
    - state/projects/PROJ-345/artifacts/
    - state/projects/PROJ-345/models/
    
    Args:
        project_root: Path to the project root directory
    """
    state_base = project_root / "state"
    projects_base = state_base / "projects"
    project_dir = projects_base / "PROJ-345"
    
    # Create subdirectories
    (project_dir / "logs").mkdir(parents=True, exist_ok=True)
    (project_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    (project_dir / "models").mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files to make directories into packages
    (state_base / "__init__.py").touch(exist_ok=True)
    (projects_base / "__init__.py").touch(exist_ok=True)
    (project_dir / "__init__.py").touch(exist_ok=True)
    (project_dir / "logs" / "__init__.py").touch(exist_ok=True)
    (project_dir / "artifacts" / "__init__.py").touch(exist_ok=True)
    (project_dir / "models" / "__init__.py").touch(exist_ok=True)
    
    print(f"Created state directory structure at: {project_dir}")


def main() -> None:
    """Entry point for creating state directories."""
    # Determine project root (parent of code/ directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    create_state_directories(project_root)


if __name__ == "__main__":
    main()
