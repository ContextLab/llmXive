import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Import the functions to test
from scripts.checksum_artifacts import (
    calculate_sha256,
    verify_artifacts,
    write_checksum_manifest
)

class TestCalculateSha256:
    def test_calculate_sha256_valid_file(self, tmp_path):
        """Test SHA256 calculation on a valid file."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        content = b"Hello, World!"
        test_file.write_bytes(content)
        
        # Calculate checksum
        checksum = calculate_sha256(test_file)
        
        # Verify against expected value
        expected = hashlib.sha256(content).hexdigest()
        assert checksum == expected
    
    def test_calculate_sha256_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        nonexistent = tmp_path / "does_not_exist.txt"
        with pytest.raises(FileNotFoundError):
            calculate_sha256(nonexistent)

class TestVerifyArtifacts:
    def test_verify_artifacts_empty_directory(self, tmp_path):
        """Test verification on an empty directory."""
        results = verify_artifacts([str(tmp_path)])
        assert results['status'] == 'success'
        assert len(results['artifacts']) == 0
        assert len(results['missing']) == 0
    
    def test_verify_artifacts_with_files(self, tmp_path):
        """Test verification with actual files."""
        # Create test files
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("id,value\n1,100\n")
        
        json_file = tmp_path / "test.json"
        json_file.write_text('{"key": "value"}')
        
        pkl_file = tmp_path / "test.pkl"
        pkl_file.write_bytes(b"pickle_data")
        
        results = verify_artifacts([str(tmp_path)], extensions=[".csv", ".json", ".pkl"])
        
        assert results['status'] == 'success'
        assert len(results['artifacts']) == 3
        
        # Verify checksums are present
        for artifact in results['artifacts']:
            assert 'sha256' in artifact
            assert 'size_bytes' in artifact
            assert artifact['path']
    
    def test_verify_artifacts_missing_critical_files(self, tmp_path):
        """Test that missing critical files are reported."""
        # Create a subdirectory structure but no critical files
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        
        results = verify_artifacts([str(tmp_path / "data")], extensions=[".csv", ".json"])
        
        # Should report missing critical files
        assert len(results['missing']) > 0
        assert any('ground_truth.csv' in m for m in results['missing'])

class TestWriteChecksumManifest:
    def test_write_checksum_manifest(self, tmp_path):
        """Test writing a checksum manifest."""
        # Create test artifacts
        artifacts = [
            {
                "path": "data/test.csv",
                "size_bytes": 100,
                "sha256": "abc123",
                "type": ".csv"
            },
            {
                "path": "models/test.pkl",
                "size_bytes": 200,
                "sha256": "def456",
                "type": ".pkl"
            }
        ]
        
        output_path = tmp_path / "manifest.json"
        write_checksum_manifest(artifacts, output_path)
        
        # Verify manifest was written
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            manifest = json.load(f)
        
        assert manifest['total_artifacts'] == 2
        assert len(manifest['artifacts']) == 2
        assert 'generated_at' in manifest

class TestIntegration:
    def test_full_verification_flow(self, tmp_path):
        """Test the full verification flow with mixed results."""
        # Setup directory structure
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        models_dir = tmp_path / "models"
        models_dir.mkdir()
        
        # Create some valid files
        (data_dir / "ground_truth.csv").write_text("id,outcome\n1,pass\n")
        (data_dir / "features.csv").write_text("id,metric\n1,0.5\n")
        (models_dir / "model.pkl").write_bytes(b"model_data")
        
        # Run verification
        results = verify_artifacts(
            [str(tmp_path / "data"), str(tmp_path / "models")],
            extensions=[".csv", ".pkl"]
        )
        
        # Should have found files but missing critical ones
        assert len(results['artifacts']) == 3
        assert len(results['missing']) > 0  # Missing decision_boundary.pkl, etc.
        assert results['status'] == 'failed'  # Because critical files are missing
        
        # Write manifest
        manifest_path = tmp_path / "checksum_manifest.json"
        write_checksum_manifest(results['artifacts'], manifest_path)
        assert manifest_path.exists()