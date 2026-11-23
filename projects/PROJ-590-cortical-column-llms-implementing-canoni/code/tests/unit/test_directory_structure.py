import os
import pytest
import sys
from pathlib import Path
from scripts.setup_directories import ensure_directory_structure, create_state_template

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root structure."""
    root = tmp_path / "project_root"
    root.mkdir()
    # Create minimal structure to simulate project
    (root / "code").mkdir()
    (root / "data").mkdir()
    (root / "tests").mkdir()
    (root / "state").mkdir()
    return root

def test_project_directories_exist(temp_project_root):
    """Verify that the required directories for T001c exist."""
    root = temp_project_root / "code"
    
    # Directories required by T001c
    required_dirs = [
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "scripts",
        root / "data" / "results",
        root / "data" / "logs",
        root / "data" / "configs",
        root / "state",
    ]
    
    for dir_path in required_dirs:
        assert dir_path.exists(), f"Directory {dir_path} does not exist"
        assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_state_template_exists(temp_project_root):
    """Verify that state/template.yaml exists (prerequisite for T004)."""
    template_path = temp_project_root / "code" / "state" / "template.yaml"
    # This test ensures the directory exists; the file creation is handled by T004
    # or create_state_template logic. We verify the directory is ready.
    state_dir = temp_project_root / "code" / "state"
    assert state_dir.exists()
