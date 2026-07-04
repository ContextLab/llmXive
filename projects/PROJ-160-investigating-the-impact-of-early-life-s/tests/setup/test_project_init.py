import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
from code.setup.project_init import get_project_path, verify_and_create_structure

def test_verify_and_create_structure_creates_missing_dirs():
    """
    Test that verify_and_create_structure creates the required subdirectories
    if they are missing in a temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a fake project root in temp
        project_root = Path(tmp_dir) / "test_project"
        project_root.mkdir()

        # Verify structure
        result = verify_and_create_structure(project_root)

        # Assertions
        assert result["success"] is True
        assert len(result["created_or_verified"]) == 5

        # Check specific directories exist
        assert (project_root / "code").exists()
        assert (project_root / "data").exists()
        assert (project_root / "data/raw").exists()
        assert (project_root / "data/processed").exists()
        assert (project_root / "tests").exists()
        assert (project_root / "contracts").exists()

def test_verify_and_create_structure_handles_existing_dirs():
    """
    Test that verify_and_create_structure does not fail if directories already exist.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir) / "test_project_2"
        project_root.mkdir()

        # Pre-create some directories
        (project_root / "code").mkdir()
        (project_root / "data").mkdir()
        (project_root / "data/raw").mkdir()

        result = verify_and_create_structure(project_root)

        assert result["success"] is True
        # Should still report 5 paths verified
        assert len(result["created_or_verified"]) == 5

def test_get_project_path_fallback():
    """
    Test get_project_path fallback behavior when project doesn't exist yet.
    """
    # This test relies on the function defaulting to current dir if not found
    # which is acceptable behavior for the setup script.
    path = get_project_path("non_existent_test_proj_xyz")
    assert path is not None
    assert path.name == "non_existent_test_proj_xyz"