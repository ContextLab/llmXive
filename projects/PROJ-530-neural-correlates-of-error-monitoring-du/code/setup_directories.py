"""
Directory setup module for project initialization.
"""
import os
from pathlib import Path

def create_project_directories(base_path: str) -> None:
    """
    Create the standard project directory structure.

    Args:
        base_path: Base path for the project (e.g., 'projects/PROJ-530-...').
    """
    base = Path(base_path)

    # Data directories
    (base / 'data' / 'raw').mkdir(parents=True, exist_ok=True)
    (base / 'data' / 'processed').mkdir(parents=True, exist_ok=True)

    # Results directories
    (base / 'results' / 'models').mkdir(parents=True, exist_ok=True)
    (base / 'results' / 'figures').mkdir(parents=True, exist_ok=True)
    (base / 'results' / 'diagnostics').mkdir(parents=True, exist_ok=True)

    # Code and tests directories
    (base / 'code').mkdir(parents=True, exist_ok=True)
    (base / 'tests').mkdir(parents=True, exist_ok=True)

    # Create __init__.py files
    (base / 'code' / '__init__.py').touch()
    (base / 'tests' / '__init__.py').touch()

    print(f"Project directories created at {base}")