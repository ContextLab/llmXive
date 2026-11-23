import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Import the function to test
# We need to adjust the import path based on where tests run from
# Assuming tests run from project root, we add code/utils to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.hash_artifacts import compute_sha256, hash_artifacts

class TestHashArtifacts:
    @pytest.fixture
    def temp_project_structure(self, tmp_path):
        """Create a temporary project structure with mock artifacts."""
        # Create directories
        data_final = tmp_path / "data" / "final"
        docs = tmp_path / "docs"
        state = tmp_path / "state"
        data_final.mkdir(parents=True)
        docs.mkdir(parents=True)
        state.mkdir(parents=True)

        # Create mock artifacts
        (data_final / "model.parquet").write_text("mock parquet data")
        (data_final / "metrics.json").write_text('{"key": "value"}')
        (docs / "final_report.md").write_text("# Final Report")

        return tmp_path

    def test_compute_sha256(self, temp_project_structure):
        """Test SHA256 computation on a known string."""
        file_path = temp_project_structure / "data" / "final" / "metrics.json"
        expected_hash = hashlib.sha256(b'{"key": "value"}').hexdigest()
        computed_hash = compute_sha256(file_path)
        assert computed_hash == expected_hash

    def test_compute_sha256_missing_file(self, temp_project_structure):
        """Test that compute_sha256 raises FileNotFoundError for missing files."""
        missing_path = temp_project_structure / "data" / "final" / "nonexistent.parquet"
        with pytest.raises(FileNotFoundError):
            compute_sha256(missing_path)

    def test_hash_artifacts_creates_output(self, temp_project_structure, monkeypatch):
        """Test that hash_artifacts creates the output JSON file."""
        # Monkeypatch the paths to use the temp directory
        import utils.hash_artifacts as ha_module
        
        original_root = ha_module.PROJECT_ROOT
        original_data_final = ha_module.DATA_FINAL_DIR
        original_docs = ha_module.DOCS_DIR
        original_state = ha_module.STATE_DIR

        ha_module.PROJECT_ROOT = temp_project_structure
        ha_module.DATA_FINAL_DIR = temp_project_structure / "data" / "final"
        ha_module.DOCS_DIR = temp_project_structure / "docs"
        ha_module.STATE_DIR = temp_project_structure / "state"

        try:
            result = hash_artifacts()
            
            output_path = temp_project_structure / "state" / "final_artifacts_hashes.json"
            assert output_path.exists(), "Output JSON file was not created"
            
            with open(output_path, "r") as f:
                data = json.load(f)
            
            assert "data/final/model.parquet" in data
            assert "data/final/metrics.json" in data
            assert "docs/final_report.md" in data
            
            # Verify the hash for metrics.json
            expected_metrics_hash = hashlib.sha256(b'{"key": "value"}').hexdigest()
            assert data["data/final/metrics.json"] == expected_metrics_hash

        finally:
            # Restore original paths
            ha_module.PROJECT_ROOT = original_root
            ha_module.DATA_FINAL_DIR = original_data_final
            ha_module.DOCS_DIR = original_docs
            ha_module.STATE_DIR = original_state