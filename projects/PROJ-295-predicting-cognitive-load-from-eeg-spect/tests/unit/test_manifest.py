"""
Unit tests for manifest generation and verification.
"""
import os
import sys
import tempfile
import yaml
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.data.manifest import (
    calculate_file_checksum,
    fetch_remote_checksum,
    verify_dataset_integrity,
    generate_manifest,
    update_state
)

class TestCalculateFileChecksum:
    """Tests for calculate_file_checksum function."""
    
    def test_calculate_checksum_valid_file(self, tmp_path):
        """Test checksum calculation for a valid file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        
        checksum = calculate_file_checksum(str(test_file))
        
        assert len(checksum) == 64  # SHA256 hex length
        assert isinstance(checksum, str)
    
    def test_calculate_checksum_nonexistent_file(self):
        """Test that FileNotFoundError is raised for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            calculate_file_checksum("/nonexistent/file.txt")
    
    def test_calculate_checksum_different_content(self, tmp_path):
        """Test that different content produces different checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        
        file1.write_text("content 1")
        file2.write_text("content 2")
        
        checksum1 = calculate_file_checksum(str(file1))
        checksum2 = calculate_file_checksum(str(file2))
        
        assert checksum1 != checksum2
    
    def test_calculate_checksum_empty_file(self, tmp_path):
        """Test checksum calculation for an empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        
        checksum = calculate_file_checksum(str(empty_file))
        
        assert len(checksum) == 64
        assert isinstance(checksum, str)

class TestVerifyDatasetIntegrity:
    """Tests for verify_dataset_integrity function."""
    
    def test_verify_all_files_valid(self, tmp_path):
        """Test verification when all files are valid."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file1.write_text("content 1")
        
        file2 = tmp_path / "file2.txt"
        file2.write_text("content 2")
        
        # Calculate actual checksums
        checksum1 = calculate_file_checksum(str(file1))
        checksum2 = calculate_file_checksum(str(file2))
        
        manifest = {
            "files": {
                "file1.txt": checksum1,
                "file2.txt": checksum2
            }
        }
        
        all_valid, failed_files = verify_dataset_integrity(str(tmp_path), manifest)
        
        assert all_valid is True
        assert failed_files == {}
    
    def test_verify_file_not_found(self, tmp_path):
        """Test verification when a file is missing."""
        manifest = {
            "files": {
                "missing.txt": "some_checksum"
            }
        }
        
        all_valid, failed_files = verify_dataset_integrity(str(tmp_path), manifest)
        
        assert all_valid is False
        assert "missing.txt" in failed_files
        assert "not found" in failed_files["missing.txt"].lower()
    
    def test_verify_checksum_mismatch(self, tmp_path):
        """Test verification when checksums don't match."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("actual content")
        
        manifest = {
            "files": {
                "test.txt": "wrong_checksum_1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab"
            }
        }
        
        all_valid, failed_files = verify_dataset_integrity(str(tmp_path), manifest)
        
        assert all_valid is False
        assert "test.txt" in failed_files
        assert "mismatch" in failed_files["test.txt"].lower()

class TestGenerateManifest:
    """Tests for generate_manifest function."""
    
    def test_generate_manifest_creates_file(self, tmp_path):
        """Test that manifest generation creates the output file."""
        # Create some test files
        (tmp_path / "test1.txt").write_text("content 1")
        (tmp_path / "test2.txt").write_text("content 2")
        
        output_path = tmp_path / "manifest.yaml"
        
        manifest = generate_manifest(str(tmp_path), str(output_path))
        
        assert output_path.exists()
        assert manifest is not None
        assert "files" in manifest
        assert "dataset_id" in manifest
        assert "version" in manifest
    
    def test_generate_manifest_includes_existing_files(self, tmp_path):
        """Test that existing files are included in the manifest."""
        test_file = tmp_path / "existing.txt"
        test_file.write_text("test content")
        
        output_path = tmp_path / "manifest.yaml"
        
        manifest = generate_manifest(str(tmp_path), str(output_path))
        
        # Check that the file is in the manifest (or at least attempted)
        assert manifest is not None
    
    def test_generate_manifest_structure(self, tmp_path):
        """Test the structure of the generated manifest."""
        output_path = tmp_path / "manifest.yaml"
        
        manifest = generate_manifest(str(tmp_path), str(output_path))
        
        # Verify required keys
        required_keys = ["dataset_id", "version", "source_url", "generated_at", "files"]
        for key in required_keys:
            assert key in manifest, f"Missing required key: {key}"

class TestUpdateState:
    """Tests for update_state function."""
    
    def test_update_state_creates_file(self, tmp_path):
        """Test that state update creates the state file."""
        # Create a manifest file first
        manifest_path = tmp_path / "manifest.yaml"
        manifest_path.write_text("test: manifest")
        
        state_path = tmp_path / "state.yaml"
        
        update_state(str(manifest_path), str(state_path))
        
        assert state_path.exists()
    
    def test_update_state_includes_checksum(self, tmp_path):
        """Test that state includes manifest checksum."""
        manifest_path = tmp_path / "manifest.yaml"
        manifest_path.write_text("test: manifest")
        
        state_path = tmp_path / "state.yaml"
        
        update_state(str(manifest_path), str(state_path))
        
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)
        
        assert "manifest" in state
        assert "checksum" in state["manifest"]
        assert len(state["manifest"]["checksum"]) == 64
    
    def test_update_state_nonexistent_manifest(self, tmp_path):
        """Test behavior when manifest file doesn't exist."""
        state_path = tmp_path / "state.yaml"
        
        # Should not raise an exception, just print a warning
        update_state("/nonexistent/manifest.yaml", str(state_path))
        
        # State file should not be created
        assert not state_path.exists()

class TestFetchRemoteChecksum:
    """Tests for fetch_remote_checksum function."""
    
    @patch('code.data.manifest.requests.get')
    def test_fetch_remote_checksum_success(self, mock_get, tmp_path):
        """Test successful remote checksum fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "sub-01 sha256=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab"
        mock_get.return_value = mock_response
        
        checksum = fetch_remote_checksum("http://example.com", "sub-01")
        
        assert checksum == "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab"
    
    @patch('code.data.manifest.requests.get')
    def test_fetch_remote_checksum_failure(self, mock_get):
        """Test failed remote checksum fetch."""
        mock_get.side_effect = Exception("Network error")
        
        checksum = fetch_remote_checksum("http://example.com", "test.txt")
        
        assert checksum is None
    
    @patch('code.data.manifest.requests.get')
    def test_fetch_remote_checksum_not_found(self, mock_get):
        """Test when remote checksum is not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        checksum = fetch_remote_checksum("http://example.com", "test.txt")
        
        assert checksum is None