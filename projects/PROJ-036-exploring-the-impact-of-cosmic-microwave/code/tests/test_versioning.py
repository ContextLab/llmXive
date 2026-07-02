"""
Tests for the versioning utility.
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
import yaml
import sys

# Add parent directory to path to allow imports from code/utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.versioning import calculate_sha256, find_artifacts, get_project_state_path, update_artifact_hashes, PROJECT_ROOT, TARGET_PROJECT_ID

class TestVersioningUtils:
    """Test cases for versioning utilities."""

    def test_calculate_sha256(self, tmp_path):
        """Test that SHA256 is calculated correctly."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        # Known SHA256 for "Hello, World!"
        expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        
        result = calculate_sha256(test_file)
        assert result == expected_hash

    def test_find_artifacts_excludes_pycache(self, tmp_path):
        """Test that __pycache__ directories are excluded."""
        # Create a structure with __pycache__
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        pycache_dir = code_dir / "__pycache__"
        pycache_dir.mkdir()
        
        # Create a real file
        real_file = code_dir / "script.py"
        real_file.write_text("print('hello')")
        
        # Create a pycache file
        pyc_file = pycache_dir / "script.cpython-311.pyc"
        pyc_file.write_bytes(b"fake pyc")
        
        # Temporarily override PROJECT_ROOT for this test
        original_root = PROJECT_ROOT
        import utils.versioning as v_module
        v_module.PROJECT_ROOT = tmp_path
        
        try:
            artifacts = find_artifacts(tmp_path)
            # Should find the .py file
            assert len(artifacts) == 1
            assert artifacts[0].name == "script.py"
            # Should NOT find the .pyc file
            assert not any(p.name.endswith(".pyc") for p in artifacts)
        finally:
            v_module.PROJECT_ROOT = original_root

    def test_update_artifact_hashes_creates_file(self, tmp_path, tmp_path_state):
        """Test that update_artifact_hashes creates the state file."""
        # Create a dummy artifact
        dummy_artifact = tmp_path / "dummy.txt"
        dummy_artifact.write_text("test content")
        
        # Setup state directory structure
        state_project_dir = tmp_path / "state" / "projects" / TARGET_PROJECT_ID
        state_project_dir.mkdir(parents=True)
        
        # Temporarily override paths
        import utils.versioning as v_module
        original_root = v_module.PROJECT_ROOT
        original_state_dir = v_module.STATE_DIR
        
        v_module.PROJECT_ROOT = tmp_path
        v_module.STATE_DIR = tmp_path / "state" / "projects"
        
        try:
            state = update_artifact_hashes(TARGET_PROJECT_ID, [dummy_artifact])
            
            # Verify state file exists
            state_file = v_module.get_project_state_path(TARGET_PROJECT_ID)
            assert state_file.exists()
            
            # Verify content
            with open(state_file, "r") as f:
                loaded = yaml.safe_load(f)
            
            assert loaded["project_id"] == TARGET_PROJECT_ID
            assert "artifacts" in loaded
            assert str(dummy_artifact.relative_to(tmp_path)) in loaded["artifacts"]
        finally:
            v_module.PROJECT_ROOT = original_root
            v_module.STATE_DIR = original_state_dir

    def test_ignore_raw_data(self, tmp_path):
        """Test that raw data files are ignored."""
        # Create raw data structure
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        raw_file = raw_dir / "planck.fits"
        raw_file.write_text("fake fits")
        
        # Create processed data
        proc_dir = tmp_path / "data" / "processed"
        proc_dir.mkdir(parents=True)
        proc_file = proc_dir / "result.csv"
        proc_file.write_text("col1,col2\n1,2")
        
        import utils.versioning as v_module
        original_root = v_module.PROJECT_ROOT
        v_module.PROJECT_ROOT = tmp_path
        
        try:
            artifacts = find_artifacts(tmp_path)
            
            # Should NOT include raw file
            assert not any("raw" in str(p) for p in artifacts)
            # Should include processed file
            assert any("processed" in str(p) for p in artifacts)
        finally:
            v_module.PROJECT_ROOT = original_root

# Fixtures for test isolation
@pytest.fixture
def tmp_path_state(tmp_path):
    """Create a temporary state directory structure."""
    state_dir = tmp_path / "state" / "projects"
    state_dir.mkdir(parents=True)
    return state_dir
