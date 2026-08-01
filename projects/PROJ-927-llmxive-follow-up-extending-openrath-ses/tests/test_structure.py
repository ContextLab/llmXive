import os
from pathlib import Path

def test_project_structure_exists():
    """Verify that all required directories from T001 exist."""
    base_path = Path("projects/PROJ-927-llmxive-follow-up-extending-openrath-ses")
    
    required_dirs = [
        "code",
        "code/generators",
        "code/executors",
        "code/simulators",
        "code/reconstructors",
        "code/analyzers",
        "tests",
        "data/raw/workflows",
        "data/processed/event_log",
        "data/processed/session_first",
        "data/processed/results",
        "state"
    ]
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        assert full_path.exists(), f"Directory missing: {full_path}"
        assert full_path.is_dir(), f"Not a directory: {full_path}"

def test_init_files_exist():
    """Verify that __init__.py files exist in all required code/ subdirectories."""
    base_path = Path("projects/PROJ-927-llmxive-follow-up-extending-openrath-ses")
    
    init_dirs = [
        "code",
        "code/generators",
        "code/executors",
        "code/simulators",
        "code/reconstructors",
        "code/analyzers",
        "tests",
        "data/raw/workflows",
        "data/processed/event_log",
        "data/processed/session_first",
        "data/processed/results",
        "state"
    ]
    
    for dir_path in init_dirs:
        init_file = base_path / dir_path / "__init__.py"
        assert init_file.exists(), f"Missing __init__.py: {init_file}"
        assert init_file.is_file(), f"Not a file: {init_file}"