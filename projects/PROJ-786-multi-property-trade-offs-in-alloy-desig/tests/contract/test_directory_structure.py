"""
Contract test for directory structure creation.
Ensures that the project adheres to the required folder layout defined in T001e.
"""
import os
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    return Path.cwd()

def test_specs_directory_exists(project_root):
    """
    Contract: The path projects/PROJ-786-multi-property-trade-offs-in-alloy-desig/specs/001-multi-property-trade-offs/
    must exist.
    """
    target_path = project_root / "projects" / "PROJ-786-multi-property-trade-offs-in-alloy-desig" / "specs" / "001-multi-property-trade-offs"
    
    assert target_path.exists(), f"Contract failed: Directory {target_path} does not exist."
    assert target_path.is_dir(), f"Contract failed: {target_path} is not a directory."

def test_specs_directory_has_gitkeep(project_root):
    """
    Contract: The specs directory must contain a .gitkeep file to ensure git tracking.
    """
    target_path = project_root / "projects" / "PROJ-786-multi-property-trade-offs-in-alloy-desig" / "specs" / "001-multi-property-trade-offs"
    gitkeep_path = target_path / ".gitkeep"
    
    assert gitkeep_path.exists(), f"Contract failed: {gitkeep_path} does not exist."
    assert gitkeep_path.is_file(), f"Contract failed: {gitkeep_path} is not a file."
