"""
Unit tests for the download_data module.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module to test
import code.download_data as download_data_module


class TestFetchCodexglueDataset:
    """Tests for fetch_codexglue_dataset function."""

    @patch('code.download_data.load_dataset')
    def test_fetch_dataset_success(self, mock_load_dataset):
        """Test successful dataset fetching."""
        # Mock dataset object
        mock_dataset = MagicMock()
        mock_dataset.to_list.return_value = [
            {"prompt": "def hello(): pass", "code": "print('hello')"},
            {"prompt": "def add(a, b): return a + b", "code": "def add(a, b): return a + b"}
        ]
        mock_load_dataset.return_value = mock_dataset

        result = download_data_module.fetch_codexglue_dataset()
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert "prompt" in result[0]
        assert "code" in result[0]
        mock_load_dataset.assert_called_once()

    @patch('code.download_data.load_dataset')
    def test_fetch_dataset_with_max_samples(self, mock_load_dataset):
        """Test fetching with max_samples limit."""
        mock_dataset = MagicMock()
        mock_dataset.to_list.return_value = [{"prompt": "p", "code": "c"} for _ in range(100)]
        mock_load_dataset.return_value = mock_dataset

        result = download_data_module.fetch_codexglue_dataset(max_samples=10)
        
        assert len(result) == 10

    @patch('code.download_data.load_dataset')
    def test_fetch_dataset_streaming(self, mock_load_dataset):
        """Test fetching with streaming mode."""
        mock_dataset_iter = iter([
            {"prompt": "p1", "code": "c1"},
            {"prompt": "p2", "code": "c2"}
        ])
        mock_load_dataset.return_value = mock_dataset_iter

        result = download_data_module.fetch_codexglue_dataset(streaming=True, max_samples=2)
        
        assert len(result) == 2

    def test_fetch_dataset_import_error(self):
        """Test handling of missing datasets library."""
        with patch.dict('sys.modules', {'datasets': None}):
            with pytest.raises(ImportError):
                download_data_module.fetch_codexglue_dataset()


class TestComputeFileHash:
    """Tests for compute_file_hash function."""

    def test_compute_hash(self):
        """Test hash computation for a known file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            hash_val = download_data_module.compute_file_hash(temp_path)
            assert len(hash_val) == 64  # SHA-256 hex length
            assert isinstance(hash_val, str)
        finally:
            os.unlink(temp_path)


class TestValidateSampleSize:
    """Tests for validate_sample_size function."""

    def test_sample_size_sufficient(self):
        """Test validation with sufficient samples."""
        data = [{"id": i} for i in range(250)]
        assert download_data_module.validate_sample_size(data, min_required=200) is True

    def test_sample_size_insufficient(self):
        """Test validation with insufficient samples."""
        data = [{"id": i} for i in range(100)]
        assert download_data_module.validate_sample_size(data, min_required=200) is False


class TestVerifyBaselineExists:
    """Tests for verify_baseline_exists function."""

    def test_baseline_exists(self):
        """Test when baseline file exists."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'{}')
            temp_path = Path(f.name)
        
        try:
            assert download_data_module.verify_baseline_exists(temp_path) is True
        finally:
            os.unlink(temp_path)

    def test_baseline_not_exists(self):
        """Test when baseline file does not exist."""
        fake_path = Path("/nonexistent/path/baseline.json")
        assert download_data_module.verify_baseline_exists(fake_path) is False


class TestSaveDataset:
    """Tests for save_dataset function."""

    def test_save_dataset(self):
        """Test saving dataset to JSONL."""
        data = [
            {"prompt": "p1", "code": "c1"},
            {"prompt": "p2", "code": "c2"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.jsonl"
            download_data_module.save_dataset(data, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2
                
                # Verify JSON structure
                first_line = json.loads(lines[0])
                assert first_line["prompt"] == "p1"
                assert first_line["code"] == "c1"


class TestValidateChecksum:
    """Tests for validate_checksum function."""

    def test_checksum_match(self):
        """Test when checksum matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "data.jsonl"
            checksum_path = Path(tmpdir) / "checksums.json"
            
            # Write data
            with open(data_path, 'w') as f:
                f.write("test data")
            
            # Compute and store hash
            file_hash = download_data_module.compute_file_hash(data_path)
            with open(checksum_path, 'w') as f:
                json.dump({"data.jsonl": file_hash}, f)
            
            assert download_data_module.validate_checksum(data_path, checksum_path) is True

    def test_checksum_mismatch(self):
        """Test when checksum does not match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "data.jsonl"
            checksum_path = Path(tmpdir) / "checksums.json"
            
            # Write data
            with open(data_path, 'w') as f:
                f.write("test data")
            
            # Store wrong hash
            with open(checksum_path, 'w') as f:
                json.dump({"data.jsonl": "wrong_hash_value"}, f)
            
            assert download_data_module.validate_checksum(data_path, checksum_path) is False

    def test_no_checksum_file(self):
        """Test when no checksum file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "data.jsonl"
            checksum_path = Path(tmpdir) / "checksums.json"
            
            # Write data
            with open(data_path, 'w') as f:
                f.write("test data")
            
            # No checksum file created
            assert download_data_module.validate_checksum(data_path, checksum_path) is True