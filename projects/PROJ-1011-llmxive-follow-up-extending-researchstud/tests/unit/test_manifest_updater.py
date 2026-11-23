"""
Unit tests for the manifest updater utility (T048).
Tests the functionality of updating state/manifest.yaml with artifact checksums.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
import yaml

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.manifest_updater import scan_artifacts, update_manifest_with_checksums
from utils.data_manifest import load_manifest, save_manifest, calculate_file_checksum


class TestScanArtifacts:
    """Tests for the scan_artifacts function."""

    def test_scan_all_files(self, tmp_path):
        """Test scanning for all files in a directory."""
        # Create test structure
        (tmp_path / "raw").mkdir()
        (tmp_path / "processed").mkdir()
        (tmp_path / "raw" / "file1.txt").write_text("content1")
        (tmp_path / "raw" / "file2.json").write_text("{}")
        (tmp_path / "processed" / "file3.csv").write_text("a,b")
        
        artifacts = scan_artifacts(tmp_path)
        
        assert len(artifacts) == 3
        assert all(isinstance(p, Path) for p in artifacts)
        assert all(p.parent.exists() for p in artifacts)

    def test_scan_specific_extensions(self, tmp_path):
        """Test scanning for specific file extensions."""
        (tmp_path / "raw").mkdir()
        (tmp_path / "raw" / "file1.txt").write_text("content1")
        (tmp_path / "raw" / "file2.json").write_text("{}")
        (tmp_path / "raw" / "file3.csv").write_text("a,b")
        
        artifacts = scan_artifacts(tmp_path, extensions=[".json", ".csv"])
        
        assert len(artifacts) == 2
        assert all(p.suffix in [".json", ".csv"] for p in artifacts)

    def test_scan_empty_directory(self, tmp_path):
        """Test scanning an empty directory."""
        artifacts = scan_artifacts(tmp_path)
        assert len(artifacts) == 0

    def test_skip_hidden_directories(self, tmp_path):
        """Test that hidden directories are skipped."""
        (tmp_path / "raw").mkdir()
        (tmp_path / ".hidden").mkdir()
        (tmp_path / "raw" / "file1.txt").write_text("content1")
        (tmp_path / ".hidden" / "file2.txt").write_text("content2")
        
        artifacts = scan_artifacts(tmp_path)
        
        assert len(artifacts) == 1
        assert "file1.txt" in str(artifacts[0])
        assert ".hidden" not in str(artifacts[0])


class TestUpdateManifestWithChecksums:
    """Tests for the update_manifest_with_checksums function."""

    @pytest.fixture
    def sample_manifest(self, tmp_path):
        """Create a sample manifest file."""
        manifest = {
            "version": "1.0",
            "metadata": {
                "created_at": "2024-01-01",
                "project": "PROJ-1011"
            },
            "files": {}
        }
        manifest_path = tmp_path / "manifest.yaml"
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f)
        return manifest_path

    @pytest.fixture
    def sample_data_dir(self, tmp_path):
        """Create a sample data directory with files."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "raw").mkdir()
        (data_dir / "processed").mkdir()
        
        # Create sample files
        (data_dir / "raw" / "test1.jsonl").write_text('{"id": 1}\n{"id": 2}')
        (data_dir / "raw" / "test2.csv").write_text("col1,col2\nval1,val2")
        (data_dir / "processed" / "result.json").write_text('{"status": "ok"}')
        
        return data_dir

    def test_update_manifest_creates_entries(self, sample_manifest, sample_data_dir):
        """Test that manifest is updated with file checksums."""
        result = update_manifest_with_checksums(sample_manifest, sample_data_dir)
        
        assert 'files' in result
        assert len(result['files']) == 3
        
        # Check that checksums are present and valid
        for rel_path, file_info in result['files'].items():
            assert 'checksum' in file_info
            assert len(file_info['checksum']) == 64  # SHA-256 hex length
            assert 'size_bytes' in file_info
            assert file_info['size_bytes'] > 0

    def test_checksum_accuracy(self, sample_manifest, sample_data_dir):
        """Test that calculated checksums match expected values."""
        result = update_manifest_with_checksums(sample_manifest, sample_data_dir)
        
        # Verify one specific file
        jsonl_path = sample_data_dir / "raw" / "test1.jsonl"
        expected_checksum = calculate_file_checksum(jsonl_path)
        
        assert result['files']['raw/test1.jsonl']['checksum'] == expected_checksum

    def test_manifest_metadata_updated(self, sample_manifest, sample_data_dir):
        """Test that manifest metadata is updated."""
        result = update_manifest_with_checksums(sample_manifest, sample_data_dir)
        
        assert 'metadata' in result
        assert 'total_files' in result['metadata']
        assert result['metadata']['total_files'] == 3
        assert 'last_updated' in result['metadata']
        assert 'scan_directory' in result['metadata']

    def test_persistent_manifest_update(self, sample_manifest, sample_data_dir):
        """Test that the manifest file is actually updated on disk."""
        update_manifest_with_checksums(sample_manifest, sample_data_dir)
        
        # Reload and verify
        reloaded = load_manifest(sample_manifest)
        
        assert 'files' in reloaded
        assert len(reloaded['files']) == 3
        assert 'raw/test1.jsonl' in reloaded['files']

    def test_handles_empty_data_dir(self, sample_manifest, tmp_path):
        """Test updating manifest when data directory is empty."""
        empty_data_dir = tmp_path / "data"
        empty_data_dir.mkdir()
        
        result = update_manifest_with_checksums(sample_manifest, empty_data_dir)
        
        assert 'files' in result
        assert len(result['files']) == 0
        assert result['metadata']['total_files'] == 0


class TestManifestIntegration:
    """Integration tests for manifest updates."""

    def test_full_workflow(self, tmp_path):
        """Test the complete workflow of creating and updating a manifest."""
        # Setup
        manifest_path = tmp_path / "state" / "manifest.yaml"
        manifest_path.parent.mkdir()
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        
        # Create initial manifest
        initial_manifest = {
            "version": "1.0",
            "metadata": {"created_at": "2024-01-01"},
            "files": {}
        }
        with open(manifest_path, 'w') as f:
            yaml.dump(initial_manifest, f)
        
        # Create data files
        (data_dir / "file1.json").write_text('{"data": 1}')
        (data_dir / "file2.csv").write_text("a,b\n1,2")
        
        # Update manifest
        result = update_manifest_with_checksums(manifest_path, data_dir)
        
        # Verify
        assert len(result['files']) == 2
        
        # Verify checksums are correct
        file1_path = data_dir / "file1.json"
        expected_checksum = calculate_file_checksum(file1_path)
        assert result['files']['file1.json']['checksum'] == expected_checksum

    def test_manifest_version_preserved(self, tmp_path):
        """Test that manifest version is preserved during updates."""
        manifest_path = tmp_path / "manifest.yaml"
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "test.txt").write_text("content")
        
        initial_manifest = {
            "version": "2.5.1",
            "metadata": {},
            "files": {}
        }
        with open(manifest_path, 'w') as f:
            yaml.dump(initial_manifest, f)
        
        update_manifest_with_checksums(manifest_path, data_dir)
        
        reloaded = load_manifest(manifest_path)
        assert reloaded['version'] == "2.5.1"