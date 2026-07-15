"""
Unit tests for the checksums hygiene module.
"""
import hashlib
import json
import tempfile
import os
from pathlib import Path
import pytest

# Mocking the config loader to avoid dependency on full project state in unit tests
import sys
from unittest.mock import patch, MagicMock

# Import the module under test
# We need to ensure the path is set up correctly if running from root
# Assuming standard project structure where tests/unit is sibling to code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from hygiene.checksums import compute_sha256, get_raw_data_files, record_checksums, load_existing_checksums, run_checksum_pipeline

class TestComputeSha256:
    def test_compute_sha256_valid_file(self, tmp_path):
        """Test SHA256 computation on a known file."""
        test_content = b"Hello, World!"
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(test_content)
        
        expected_hash = hashlib.sha256(test_content).hexdigest()
        computed_hash = compute_sha256(test_file)
        
        assert computed_hash == expected_hash
    
    def test_compute_sha256_nonexistent_file(self):
        """Test that FileNotFoundError is raised for missing files."""
        with pytest.raises(FileNotFoundError):
            compute_sha256(Path("/nonexistent/path/file.txt"))
    
    def test_compute_sha256_large_file(self, tmp_path):
        """Test chunked reading for a larger file."""
        # Create a file larger than 4KB (our chunk size)
        size = 1024 * 1024  # 1MB
        test_content = b"A" * size
        test_file = tmp_path / "large.txt"
        test_file.write_bytes(test_content)
        
        expected_hash = hashlib.sha256(test_content).hexdigest()
        computed_hash = compute_sha256(test_file)
        
        assert computed_hash == expected_hash

class TestGetRawDataFiles:
    def test_get_raw_data_files_empty(self, tmp_path):
        """Test behavior when raw directory is empty or missing."""
        data_dir = tmp_path / "data"
        files = get_raw_data_files(data_dir)
        assert files == []
    
    def test_get_raw_data_files_with_parquet(self, tmp_path):
        """Test detection of parquet files."""
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw" / "humaneval"
        raw_dir.mkdir(parents=True)
        
        parquet_file = raw_dir / "data.parquet"
        parquet_file.write_text("dummy")
        
        files = get_raw_data_files(data_dir)
        assert len(files) == 1
        assert "data.parquet" in str(files[0])
    
    def test_get_raw_data_files_with_jsonl(self, tmp_path):
        """Test detection of jsonl files."""
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw" / "humaneval"
        raw_dir.mkdir(parents=True)
        
        jsonl_file = raw_dir / "data.jsonl"
        jsonl_file.write_text("dummy")
        
        files = get_raw_data_files(data_dir)
        assert len(files) == 1
        assert "data.jsonl" in str(files[0])

class TestRecordChecksums:
    def test_record_checksums_creates_file(self, tmp_path):
        """Test that record_checksums creates the file and directory."""
        output_file = tmp_path / "state" / "subdir" / "checksums.json"
        checksums = {"file.txt": "abc123"}
        
        record_checksums(checksums, output_file)
        
        assert output_file.exists()
        with open(output_file, "r") as f:
            data = json.load(f)
        assert data == checksums

class TestLoadExistingChecksums:
    def test_load_existing_checksums_file_exists(self, tmp_path):
        """Test loading from an existing file."""
        output_file = tmp_path / "checksums.json"
        existing_data = {"file.txt": "hash123"}
        output_file.write_text(json.dumps(existing_data))
        
        loaded = load_existing_checksums(output_file)
        assert loaded == existing_data
    
    def test_load_existing_checksums_file_missing(self, tmp_path):
        """Test loading when file does not exist."""
        output_file = tmp_path / "checksums.json"
        
        loaded = load_existing_checksums(output_file)
        assert loaded == {}

class TestRunChecksumPipeline:
    @patch("hygiene.checksums.load_config")
    @patch("hygiene.checksums.get_raw_data_files")
    @patch("hygiene.checksums.record_checksums")
    def test_run_checksum_pipeline_success(
        self, mock_record, mock_get_files, mock_load_config, tmp_path
    ):
        """Test successful pipeline execution."""
        # Setup mocks
        mock_load_config.return_value = {
            "data_root": str(tmp_path),
            "state_root": str(tmp_path / "state")
        }
        
        # Create a dummy file to simulate raw data
        raw_dir = tmp_path / "raw" / "humaneval"
        raw_dir.mkdir(parents=True)
        test_file = raw_dir / "test.parquet"
        test_file.write_text("content")
        
        mock_get_files.return_value = [test_file]
        
        # Run
        result = run_checksum_pipeline()
        
        # Verify
        assert "raw/humaneval/test.parquet" in result
        mock_record.assert_called_once()
    
    @patch("hygiene.checksums.load_config")
    @patch("hygiene.checksums.get_raw_data_files")
    def test_run_checksum_pipeline_no_files(
        self, mock_get_files, mock_load_config, tmp_path
    ):
        """Test pipeline when no files are found."""
        mock_load_config.return_value = {
            "data_root": str(tmp_path),
            "state_root": str(tmp_path / "state")
        }
        mock_get_files.return_value = []
        
        result = run_checksum_pipeline()
        
        assert result == {}
        # Verify record was called with empty dict
        # The mock_record is not patched in this specific test, so we check side effects
        # But since we didn't patch record_checksums, it will try to write.
        # Let's adjust: patch record_checksums too.
        pass

    @patch("hygiene.checksums.load_config")
    @patch("hygiene.checksums.get_raw_data_files")
    @patch("hygiene.checksums.record_checksums")
    def test_run_checksum_pipeline_no_files(
        self, mock_record, mock_get_files, mock_load_config, tmp_path
    ):
        """Test pipeline when no files are found."""
        mock_load_config.return_value = {
            "data_root": str(tmp_path),
            "state_root": str(tmp_path / "state")
        }
        mock_get_files.return_value = []
        
        result = run_checksum_pipeline()
        
        assert result == {}
        # Verify record_checksums was called with empty dict
        assert mock_record.called
        call_args = mock_record.call_args[0]
        assert call_args[0] == {}
