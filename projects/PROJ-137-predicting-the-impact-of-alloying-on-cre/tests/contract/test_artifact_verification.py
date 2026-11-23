"""
Contract Test for Artifact Verification (Task T033).

Verifies that the verification script correctly identifies missing artifacts,
computes hashes, and updates the manifest.
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest
import sys

# Add src to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from utils.hash import compute_file_hash, update_manifest
from utils.verify_artifacts import EXPECTED_ARTIFACTS


class TestArtifactVerification:
    """Tests for the artifact verification logic."""

    def test_compute_file_hash_validates_existence(self):
        """Ensure compute_file_hash raises error for non-existent files."""
        with pytest.raises(FileNotFoundError):
            compute_file_hash(Path("/non/existent/file.txt"))

    def test_compute_file_hash_returns_hex_string(self):
        """Ensure compute_file_hash returns a valid hex string."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)
        
        try:
            hash_val = compute_file_hash(tmp_path)
            assert isinstance(hash_val, str)
            assert len(hash_val) == 64  # SHA256
            assert all(c in '0123456789abcdef' for c in hash_val)
        finally:
            os.unlink(tmp_path)

    def test_update_manifest_creates_file(self):
        """Ensure update_manifest creates the manifest file if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "test_manifest.yaml"
            test_data = [{"path": "test.csv", "hash": "abc123"}]
            
            update_manifest(manifest_path, test_data)
            
            assert manifest_path.exists()
            with open(manifest_path, 'r') as f:
                loaded = yaml.safe_load(f)
            assert loaded == test_data

    def test_expected_artifacts_structure(self):
        """Ensure EXPECTED_ARTIFACTS has required fields."""
        assert len(EXPECTED_ARTIFACTS) > 0
        for artifact in EXPECTED_ARTIFACTS:
            assert "path" in artifact
            assert "type" in artifact
            assert "source_task" in artifact
            assert artifact["path"].startswith("data/") or artifact["path"].startswith("docs/")
            assert artifact["type"] in ["csv", "yaml", "json", "png", "md"]

    def test_manifest_update_idempotency(self):
        """Ensure updating manifest with same data doesn't duplicate entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "idempotent_manifest.yaml"
            initial_data = [{"path": "a.csv", "hash": "111"}]
            
            # First update
            update_manifest(manifest_path, initial_data)
            
            # Second update with same data
            update_manifest(manifest_path, initial_data)
            
            with open(manifest_path, 'r') as f:
                loaded = yaml.safe_load(f)
            
            # Should still have only one entry
            assert len(loaded) == 1
            assert loaded[0]["path"] == "a.csv"