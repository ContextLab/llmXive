import os
import pytest
from pathlib import Path

def test_required_directories_exist():
    """
    Contract test: Verify that the project structure task created the required directories.
    """
    project_root = Path.cwd()
    
    required_dirs = [
        "projects/PROJ-399-the-impact-of-framing-on-perceived-sever/data/raw",
        "data/processed",
        "results/plots",
        "code",
        "tests",
        ".github/workflows",
        "docs"
    ]

    missing = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(dir_path)

    assert len(missing) == 0, f"The following required directories are missing: {missing}"

def test_deliverable_log_exists():
    """
    Contract test: Verify that the deliverable docs/project_structure.md exists.
    """
    project_root = Path.cwd()
    log_file = project_root / "docs" / "project_structure.md"
    
    assert log_file.exists(), f"Deliverable file {log_file} does not exist."
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    assert "Project Structure Verification Log" in content, "Log file missing header."
    assert "data/processed" in content or "data/processed" in str(log_file.parent), "Log file content seems incomplete."