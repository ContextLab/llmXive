import os
from pathlib import Path

def ensure_dirs(base_path: Path) -> None:
    """
    Creates the necessary directory structure for the project if they do not exist.
    
    This function implements the directory creation logic for T002, T003, T004, T005, and T006,
    ensuring that the `code/`, `data/`, `tests/`, and their subdirectories are present.
    
    Args:
        base_path: The root path of the project (e.g., 'projects/PROJ-505-exploring...').
    """
    dirs_to_create = [
        base_path / "code",
        base_path / "data",
        base_path / "tests",
        base_path / "code" / "ingestion",
        base_path / "code" / "analysis",
        base_path / "code" / "utils",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "artifacts",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
