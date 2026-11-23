import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add project root to path if running from tests/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.hash_artifacts import compute_file_hash, scan_artifacts, generate_manifest, save_manifest, EXCLUDE_PATTERNS


class TestComputeFileHash:
    def test_compute_file_hash_success(self, tmp_path):
        """Test that a file is hashed correctly."""
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)

        hash_val = compute_file_hash(test_file)
        assert len(hash_val) == 64  # SHA256 hex length
        assert isinstance(hash_val, str)

    def test_compute_file_hash_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        missing_file = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            compute_file_hash(missing_file)

    def test_compute_file_hash_large_file(self, tmp_path):
        """Test hashing a larger file to ensure chunking works."""
        test_file = tmp_path / "large.bin"
        # Create a 1MB file
        content = b"0" * (1024 * 1024)
        test_file.write_bytes(content)

        hash_val = compute_file_hash(test_file)
        assert len(hash_val) == 64


class TestScanArtifacts:
    def test_scan_artifacts_empty_dir(self, tmp_path):
        """Test scanning an empty directory."""
        artifacts = scan_artifacts(tmp_path, [])
        assert artifacts == []

    def test_scan_artifacts_finds_files(self, tmp_path):
        """Test that scan_artifacts finds files in subdirectories."""
        sub_dir = tmp_path / "data" / "raw"
        sub_dir.mkdir(parents=True)
        test_file = sub_dir / "data.csv"
        test_file.write_text("col1,col2\n1,2")

        artifacts = scan_artifacts(tmp_path, ["data/raw"])
        assert len(artifacts) == 1
        assert artifacts[0]["path"].endswith("data.csv")
        assert artifacts[0]["hash"] is not None
        assert artifacts[0]["size"] > 0

    def test_scan_artifacts_excludes_patterns(self, tmp_path):
        """Test that files matching EXCLUDE_PATTERNS are skipped."""
        sub_dir = tmp_path / "data" / "raw"
        sub_dir.mkdir(parents=True)
        valid_file = sub_dir / "valid.txt"
        valid_file.write_text("valid")
        
        exclude_file = sub_dir / "cache.pyc"
        exclude_file.write_text("bad")

        artifacts = scan_artifacts(tmp_path, ["data/raw"])
        paths = [a["path"] for a in artifacts]
        
        assert any("valid.txt" in p for p in paths)
        assert not any("cache.pyc" in p for p in paths)

    def test_scan_artifacts_nonexistent_dir(self, tmp_path):
        """Test scanning a directory that doesn't exist."""
        # Should not raise, just return empty or skip
        artifacts = scan_artifacts(tmp_path, ["nonexistent/path"])
        assert artifacts == []


class TestGenerateManifest:
    def test_generate_manifest_structure(self, tmp_path):
        """Test that generate_manifest returns correct structure."""
        artifacts = [
            {"path": "data/test.txt", "hash": "abc123", "size": 100, "type": ".txt", "mtime": 12345}
        ]
        manifest = generate_manifest(artifacts, tmp_path)

        assert "project_root" in manifest
        assert "generated_at" in manifest
        assert "algorithm" in manifest
        assert "total_artifacts" in manifest
        assert "artifacts" in manifest
        assert manifest["total_artifacts"] == 1
        assert manifest["algorithm"] == "sha256"

    def test_generate_manifest_summary(self, tmp_path):
        """Test that manifest includes summary statistics."""
        artifacts = [
            {"path": "a.txt", "hash": "h1", "size": 100, "type": ".txt", "mtime": 1},
            {"path": "b.txt", "hash": "h2", "size": 200, "type": ".txt", "mtime": 2}
        ]
        manifest = generate_manifest(artifacts, tmp_path)

        assert manifest["summary"]["total_size_bytes"] == 300
        assert "by_type" in manifest["summary"]


class TestSaveManifest:
    def test_save_manifest_creates_file(self, tmp_path):
        """Test that save_manifest writes a valid JSON file."""
        manifest = {"test": "data", "count": 1}
        output_path = tmp_path / "state" / "manifest.json"
        
        save_manifest(manifest, output_path)
        
        assert output_path.exists()
        with open(output_path, "r") as f:
            loaded = json.load(f)
        assert loaded == manifest

    def test_save_manifest_creates_parent_dirs(self, tmp_path):
        """Test that save_manifest creates parent directories."""
        manifest = {}
        output_path = tmp_path / "deep" / "nested" / "dir" / "manifest.json"
        
        save_manifest(manifest, output_path)
        
        assert output_path.exists()
        assert output_path.parent.exists()


class TestIntegration:
    def test_full_pipeline(self, tmp_path):
        """Test the full flow: scan -> generate -> save -> verify."""
        # Setup
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        (data_dir / "file1.json").write_text('{"key": "value"}')
        (data_dir / "file2.json").write_text('{"key": 123}')

        # Run scan
        artifacts = scan_artifacts(tmp_path, ["data/processed"])
        assert len(artifacts) == 2

        # Generate manifest
        manifest = generate_manifest(artifacts, tmp_path)
        assert manifest["total_artifacts"] == 2

        # Save manifest
        output_path = tmp_path / "state" / "artifacts.json"
        save_manifest(manifest, output_path)

        # Verify
        assert output_path.exists()
        with open(output_path, "r") as f:
            saved_manifest = json.load(f)
        
        assert saved_manifest["total_artifacts"] == 2
        assert saved_manifest["algorithm"] == "sha256"
        # Verify hashes are consistent
        assert saved_manifest["artifacts"][0]["hash"] == artifacts[0]["hash"]