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

# Add the project root to the path so we can import utils
# Assuming this test file is at code/tests/test_versioning.py
# and the utils are at code/utils/
# The project root is two levels up from this file.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.versioning import calculate_sha256, find_artifacts, get_project_state_path, update_artifact_hashes, PROJECT_ROOT as utils_project_root

@pytest.fixture
def tmp_project_structure(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directory structure similar to the real project
    code_dir = tmp_path / "code" / "utils"
    config_dir = tmp_path / "config"
    data_processed_dir = tmp_path / "data" / "processed"
    state_dir = tmp_path / "state" / "projects" / "PROJ-036-test"
    
    code_dir.mkdir(parents=True)
    config_dir.mkdir(parents=True)
    data_processed_dir.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    
    # Create some dummy files
    (code_dir / "test_module.py").write_text("def hello(): pass")
    (config_dir / "test_config.yaml").write_text("key: value")
    (data_processed_dir / "results.csv").write_text("col1,col2\n1,2")
    
    # Create a file that should be ignored
    (code_dir / "__pycache__").mkdir()
    (code_dir / "__pycache__" / "cached.pyc").write_text("fake pyc")
    
    return tmp_path

class TestVersioningUtils:
    def test_calculate_sha256(self, tmp_project_structure):
        """Test SHA256 calculation for a known file."""
        test_file = tmp_project_structure / "code" / "utils" / "test_module.py"
        hash_result = calculate_sha256(test_file)
        assert len(hash_result) == 64  # SHA256 hex digest length
        assert all(c in '0123456789abcdef' for c in hash_result)

    def test_find_artifacts_excludes_ignored(self, tmp_project_structure):
        """Test that find_artifacts excludes __pycache__ and .pyc files."""
        # We need to mock the PROJECT_ROOT for the utils module to point to our tmp_path
        # Since the module uses a global PROJECT_ROOT, we temporarily patch it
        import utils.versioning
        original_root = utils.versioning.PROJECT_ROOT
        utils.versioning.PROJECT_ROOT = tmp_project_structure
        
        try:
            artifacts = find_artifacts(tmp_project_structure)
            artifact_paths = [str(p) for p in artifacts]
            
            # Check that our test files are found
            assert any("test_module.py" in p for p in artifact_paths)
            assert any("test_config.yaml" in p for p in artifact_paths)
            assert any("results.csv" in p for p in artifact_paths)
            
            # Check that ignored files are NOT found
            assert not any("__pycache__" in p for p in artifact_paths)
            assert not any(".pyc" in p for p in artifact_paths)
        finally:
            utils.versioning.PROJECT_ROOT = original_root

    def test_update_artifact_hashes_creates_file(self, tmp_project_structure):
        """Test that update_artifact_hashes creates the state file."""
        import utils.versioning
        original_root = utils.versioning.PROJECT_ROOT
        utils.versioning.PROJECT_ROOT = tmp_project_structure
        
        try:
            artifacts = find_artifacts(tmp_project_structure)
            result = update_artifact_hashes("PROJ-036-test", artifacts)
            
            state_file = get_project_state_path("PROJ-036-test")
            assert state_file.exists()
            
            # Verify content
            with open(state_file, "r") as f:
                data = yaml.safe_load(f)
            
            assert data["project_id"] == "PROJ-036-test"
            assert "artifacts" in data
            assert len(data["artifacts"]) > 0
        finally:
            utils.versioning.PROJECT_ROOT = original_root
