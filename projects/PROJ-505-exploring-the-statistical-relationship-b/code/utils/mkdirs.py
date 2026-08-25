import os
from pathlib import Path

def ensure_dirs():
    """
    Create all necessary directories for the project structure.
    This function ensures that the directory tree required for the
    solar wind composition analysis project exists.
    """
    project_root = Path("projects/PROJ-505-exploring-the-statistical-relationship-b")
    
    directories = [
        # Phase 1: Setup
        project_root,
        project_root / "code",
        project_root / "data",
        project_root / "tests",
        
        # Phase 1: Sub-directories
        project_root / "code" / "ingestion",
        project_root / "code" / "analysis",
        project_root / "code" / "utils",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "artifacts",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    return list(directories)