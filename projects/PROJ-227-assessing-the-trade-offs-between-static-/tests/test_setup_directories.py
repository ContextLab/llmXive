import os
import pytest
from pathlib import Path
from code.setup_directories import main

@pytest.fixture
def project_path():
    return Path("projects/PROJ-227-assessing-the-trade-offs-between-static-")

def test_main_creates_directories(project_path):
    """
    Test that main() creates the required directory structure.
    """
    # Ensure clean state for the test (remove if exists)
    if project_path.exists():
        import shutil
        shutil.rmtree(project_path)
    
    # Run the setup
    exit_code = main()
    
    assert exit_code == 0, "main() should return 0 on success"
    assert project_path.exists(), "Project root directory should exist"

    # Check specific subdirectories
    required_dirs = [
        project_path / "data" / "raw",
        project_path / "data" / "processed",
        project_path / "state",
        project_path / "code",
        project_path / "tests",
    ]

    for d in required_dirs:
        assert d.exists(), f"Required directory {d} should exist"
        assert d.is_dir(), f"{d} should be a directory"

def test_main_idempotent(project_path):
    """
    Test that running main() again does not fail if directories exist.
    """
    # First run creates them
    main()
    
    # Second run should succeed (idempotent)
    exit_code = main()
    assert exit_code == 0, "main() should return 0 even if directories already exist"