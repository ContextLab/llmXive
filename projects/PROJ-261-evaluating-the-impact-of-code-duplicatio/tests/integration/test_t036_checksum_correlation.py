"""
Integration test for T036: checksum computation for correlation results.

Tests that:
1. The checksum script runs without errors
2. The manifest file is created/updated correctly
3. The checksum matches the expected value for the correlation results file
"""
import hashlib
import json
import os
import tempfile
from pathlib import Path

import pytest

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestT036ChecksumCorrelation:
    """Integration tests for T036 checksum computation."""

    @pytest.fixture
    def sample_correlation_results(self, tmp_path):
        """Create a sample correlation results CSV file for testing."""
        csv_path = tmp_path / "correlation_results.csv"
        csv_content = """metric,correlation,p_value,significance
        clone_density_vs_perplexity,0.723,0.001,significant
        clone_density_vs_accuracy,-0.412,0.034,significant
        perplexity_vs_accuracy,-0.589,0.008,significant
        """
        csv_path.write_text(csv_content)
        return csv_path

    def test_compute_file_checksum(self, sample_correlation_results):
        """Test that file checksum is computed correctly."""
        from checksum_manifest import compute_file_checksum

        checksum = compute_file_checksum(sample_correlation_results, algorithm="sha256")

        assert checksum is not None
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex string length
        assert all(c in "0123456789abcdef" for c in checksum.lower())

    def test_compute_known_checksum(self, sample_correlation_results):
        """Test that computed checksum matches expected value."""
        from checksum_manifest import compute_file_checksum

        # Compute expected checksum manually
        expected_content = sample_correlation_results.read_text().encode("utf-8")
        expected_checksum = hashlib.sha256(expected_content).hexdigest()

        # Compute using our function
        actual_checksum = compute_file_checksum(sample_correlation_results, algorithm="sha256")

        assert actual_checksum == expected_checksum

    def test_record_artifact_in_manifest(self, sample_correlation_results, tmp_path):
        """Test that artifact is recorded in manifest correctly."""
        from checksum_manifest import load_manifest, record_artifact_checksums, save_manifest

        manifest_path = tmp_path / "test_manifest.json"

        # Create initial manifest
        manifest = {
            "version": "1.0",
            "created_at": None,
            "updated_at": None,
            "artifact_hashes": {},
            "metadata": {"project": "test", "task": "T036"},
        }

        # Record artifact
        artifact_key = "correlation_results.csv"
        artifact_info = {
            "path": str(sample_correlation_results),
            "checksum": "test_checksum_123",
            "algorithm": "sha256",
            "size_bytes": sample_correlation_results.stat().st_size,
            "task": "T036",
            "description": "Test correlation results",
        }

        record_artifact_checksums(manifest, artifact_key, artifact_info)

        # Verify artifact was recorded
        assert artifact_key in manifest["artifact_hashes"]
        assert manifest["artifact_hashes"][artifact_key]["checksum"] == "test_checksum_123"
        assert manifest["artifact_hashes"][artifact_key]["task"] == "T036"

    def test_save_and_load_manifest(self, sample_correlation_results, tmp_path):
        """Test that manifest can be saved and loaded correctly."""
        from checksum_manifest import load_manifest, record_artifact_checksums, save_manifest

        manifest_path = tmp_path / "test_manifest.json"

        # Create manifest with artifact
        manifest = {
            "version": "1.0",
            "created_at": None,
            "updated_at": None,
            "artifact_hashes": {},
            "metadata": {"project": "test", "task": "T036"},
        }

        artifact_key = "correlation_results.csv"
        artifact_info = {
            "path": str(sample_correlation_results),
            "checksum": "abc123",
            "algorithm": "sha256",
            "size_bytes": sample_correlation_results.stat().st_size,
            "task": "T036",
            "description": "Test",
        }

        record_artifact_checksums(manifest, artifact_key, artifact_info)
        save_manifest(manifest, manifest_path)

        # Load and verify
        loaded_manifest = load_manifest(manifest_path)

        assert loaded_manifest["version"] == "1.0"
        assert artifact_key in loaded_manifest["artifact_hashes"]
        assert loaded_manifest["artifact_hashes"][artifact_key]["checksum"] == "abc123"

    def test_nonexistent_file_checksum(self, tmp_path):
        """Test that checksum returns None for nonexistent file."""
        from checksum_manifest import compute_file_checksum

        nonexistent_path = tmp_path / "nonexistent.csv"

        checksum = compute_file_checksum(nonexistent_path, algorithm="sha256")

        assert checksum is None

    def test_manifest_json_structure(self, sample_correlation_results, tmp_path):
        """Test that manifest JSON has correct structure."""
        from checksum_manifest import load_manifest, record_artifact_checksums, save_manifest

        manifest_path = tmp_path / "test_manifest.json"

        manifest = {
            "version": "1.0",
            "created_at": None,
            "updated_at": None,
            "artifact_hashes": {},
            "metadata": {"project": "test", "task": "T036"},
        }

        artifact_key = "correlation_results.csv"
        artifact_info = {
            "path": str(sample_correlation_results),
            "checksum": "abc123",
            "algorithm": "sha256",
            "size_bytes": sample_correlation_results.stat().st_size,
            "task": "T036",
            "description": "Test",
        }

        record_artifact_checksums(manifest, artifact_key, artifact_info)
        save_manifest(manifest, manifest_path)

        # Load and validate JSON structure
        with open(manifest_path, "r") as f:
            loaded = json.load(f)

        assert "version" in loaded
        assert "artifact_hashes" in loaded
        assert "metadata" in loaded
        assert isinstance(loaded["artifact_hashes"], dict)
        assert "correlation_results.csv" in loaded["artifact_hashes"]